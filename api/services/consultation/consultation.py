#!/usr/bin/env python3

import json
from langchain.messages import HumanMessage

from services.consultation.verify_consultation import check_user
from services.consultation.clean_consultation_data import parse_json
from services.consultation.save_consultation import save_consultation
from services.consultation.save_sms import save_consultation_sms

from external_integration.agents.agent.consultation import consultation_agent
from external_integration.agents.utils.get_patient_ids import get_patient_id

from sqlalchemy.orm import Session
from models.database_models import Consultation

agent = consultation_agent()


def get_active_consultation(db: Session, patient_id: int):
    """
    Returns the latest active consultation for the given patient, if any.
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


def handle_consultation(db: Session, phone_number: str, user_input: str, thread_id: str):
    """
    Handles consultation. Reuses the last active consultation if available.
    Args:
        db: Session
        phone_number: str
        user_input: str
        thread_id: str
    """
    check_phone = check_user(phone_number=phone_number)

    if check_phone["status"] == "complete" or not check_phone["register"]:
        return {
            "status": "complete",
            "message": check_phone["current_message"],
            "consultation_id": None
        }

    patient_id = get_patient_id(phone_number=phone_number)

    # Check for latest active consultation
    active_consultation = get_active_consultation(db=db, patient_id=patient_id)

    # Decide thread_id to reuse
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

        sms_metadata = None
        if tool_call and tool_call.get("name"):
            sms_metadata = json.dumps({"tool_call": tool_call})

        save_consultation_sms(
            db=db,
            consultation_id=active_consultation.id,
            message_type="ai",
            content=ai_content,
            sms_metadata=sms_metadata,
        )

    # Update consultation
    active_consultation.risk_level = risk_level
    active_consultation.consultation_summary = consultation_summary
    active_consultation.consultation_status = is_active

    db.commit()

    return {
        "status": consultation_data.get("status"),
        "message": ai_content,
        "consultation_id": active_consultation.id,
        "thread_id": current_thread_id
    }
