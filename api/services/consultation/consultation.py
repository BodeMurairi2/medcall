#!/usr/bin/env python3

import json
from threading import Thread
from langchain_core.messages import HumanMessage

from services.consultation.clean_consultation_data import parse_json, sanitize_nan
from services.consultation.save_consultation import save_consultation
from services.consultation.save_sms import save_consultation_sms

from external_integration.agents.agent.consultation import consultation_agent
from external_integration.agents.agent.analysis import analytic_agent
from external_integration.agents.utils.normalize_phone import normalize_phone_number

from sqlalchemy.orm import Session
from models.database_models import Consultation, ConsultationSMS, ConsultationAnalysis, PatientRegistration
from database.create_session import SessionLocal


agent = consultation_agent()


def get_active_consultation(db: Session, patient_id: int):
    """
    Returns the latest active (in-progress) consultation for the given patient.
    """
    return (
        db.query(Consultation)
        .filter(
            Consultation.patient_id == patient_id,
            Consultation.consultation_status == True
        )
        .order_by(Consultation.last_updated.desc())
        .first()
    )


def trigger_analysis(consultation_id: int, patient_int_id: int, collected_data: dict):
    """
    Runs the analytic_agent in a background thread with its own db session.
    Args:
        consultation_id: integer PK of the consultation
        patient_int_id: integer PK of the patient (patients.id)
        collected_data: symptoms/severity data from the consultation
    """
    db = SessionLocal()
    try:
        consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
        if not consultation:
            print(f"[ERROR] Consultation {consultation_id} not found in analysis thread")
            return

        # Get the string patient_id (e.g. "Patient-abc123") for the tool
        patient = db.query(PatientRegistration).filter(PatientRegistration.id == patient_int_id).first()
        string_patient_id = patient.patient_id if patient else str(patient_int_id)

        agent_instance, _ = analytic_agent(thread_id=str(consultation_id))

        conversation = [
            {"type": sms.message_type, "content": sms.content}
            for sms in db.query(ConsultationSMS)
                        .filter(ConsultationSMS.consultation_id == consultation_id)
                        .all()
        ]

        analysis_input = {
            "patient_id": string_patient_id,
            "consultation_id": str(consultation_id),
            "collected_data": collected_data,
            "consultation_summary": consultation.consultation_summary,
            "conversation": conversation
        }

        analysis_response = agent_instance.invoke(
            {"messages": [HumanMessage(content=json.dumps(sanitize_nan(analysis_input)))]},
            config={"configurable": {"thread_id": str(consultation_id)}}
        )

        raw_analysis = analysis_response["messages"][-1].content
        analysis_json = parse_json(raw_content=raw_analysis)

        if isinstance(analysis_json, dict) and analysis_json:
            analysis_record = ConsultationAnalysis(
                consultation_id=consultation_id,
                detected_symptoms=json.dumps(analysis_json.get("detected_symptoms", [])),
                possible_conditions=json.dumps(analysis_json.get("possible_conditions", [])),
                exams=json.dumps(analysis_json.get("exams", {})),
                risk_level=analysis_json.get("risk_level", "low"),
                mark_emergency=analysis_json.get("mark_emergency", False),
                reasoning=analysis_json.get("reasoning", "")
            )
            db.add(analysis_record)
            db.commit()
            print(f"[INFO] Analysis saved for consultation {consultation_id}")
        else:
            print(f"[WARN] Analysis returned empty or invalid JSON for consultation {consultation_id}")

    except Exception as e:
        print(f"[ERROR] Analysis failed for consultation {consultation_id}: {e}")
    finally:
        db.close()


def handle_consultation(db: Session, phone_number: str, user_input: str, thread_id: str):
    """
    Handles a consultation turn. Reuses the last active consultation if available.
    """
    # Single query — verify registration and get patient_id in one shot
    # using the already-open db session (avoids 2 extra sessions + 2 redundant queries)
    patient = db.query(PatientRegistration).filter(
        PatientRegistration.phone_number == normalize_phone_number(phone_number)
    ).first()

    if not patient:
        return {
            "status": "complete",
            "message": "Sorry! You are not registered. Please use *384*41992# to register.",
            "consultation_id": None
        }

    patient_id = patient.id

    # Check for latest active consultation
    active_consultation = get_active_consultation(db=db, patient_id=patient_id)

    # Reuse existing thread_id or use the new one
    current_thread_id = active_consultation.thread_id if active_consultation else thread_id

    # Send user message to AI agent
    response = agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content=f"user question: {user_input}\nuser phone number: {phone_number}"
                )
            ]
        },
        config={"configurable": {"thread_id": current_thread_id}},
    )

    raw_content = response["messages"][-1].content
    consultation_result = parse_json(raw_content=raw_content)

    consultation_data = (
        consultation_result[-1]
        if isinstance(consultation_result, list)
        else consultation_result
    )

    if not isinstance(consultation_data, dict):
        return {
            "status": "error",
            "message": "Invalid AI response format",
            "consultation_id": None
        }

    collected_data = consultation_data.get("collected_data", {})
    severity = collected_data.get("severity", {})
    risk_level = ",".join(severity.values()) if severity else None

    consultation_summary = (
        consultation_data.get("consultation_summary")
        or consultation_data.get("summary")
        or ""
    )

    is_active = consultation_data.get("status", "in_progress") != "complete"

    # Create a new consultation only if no active one exists
    if not active_consultation:
        active_consultation = save_consultation(
            db=db,
            patient_id=patient_id,
            risk_level=risk_level,
            consultation_summary=consultation_summary,
            consultation_status=is_active,
            thread_id=current_thread_id
        )

        if not active_consultation:
            return {
                "status": "error",
                "message": "Failed to save consultation",
                "consultation_id": None
            }

    # Save user message
    save_consultation_sms(
        db=db,
        consultation_id=active_consultation.id,
        message_type="user",
        content=user_input,
        sms_metadata=None
    )

    # Save AI message
    ai_content = consultation_data.get("current_message")

    if ai_content:
        tool_call = consultation_data.get("tool_call")
        sms_metadata = json.dumps({"tool_call": tool_call}) if tool_call and tool_call.get("name") else None
        save_consultation_sms(
            db=db,
            consultation_id=active_consultation.id,
            message_type="ai",
            content=ai_content,
            sms_metadata=sms_metadata,
        )

    # Update consultation record
    active_consultation.risk_level = risk_level
    active_consultation.consultation_summary = consultation_summary
    active_consultation.consultation_status = is_active
    db.commit()

    # Trigger background analysis when consultation is complete
    if not is_active:
        Thread(
            target=trigger_analysis,
            args=(active_consultation.id, patient_id, collected_data),
            daemon=True
        ).start()

    return {
        "status": consultation_data.get("status"),
        "message": ai_content,
        "consultation_id": active_consultation.id,
        "thread_id": current_thread_id
    }
