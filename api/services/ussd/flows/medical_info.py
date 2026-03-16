#!/usr/bin/env python3

import bcrypt
from sqlalchemy.orm import Session
from datetime import datetime
from models.database_models import PatientRegistration, PatientMedicalInfo
from schemas.users import PatientMedicalInformation as medical_info_schema
from database.session import get_db
from services.ussd.response import con, end
from services.ussd.state import USSDMedicalInfo
from utils.blood_type import blood_type

def save_medical_info(session, user_input, db:Session):
    """Save medical information"""
    user_input = user_input.strip()
    state = session["state"]
    phone_number = session["phone"]

    existing_user = db.query(
        PatientRegistration).where(
            PatientRegistration.phone_number == phone_number).first()
    
    if not existing_user:
        return end("User not found. Register first before using MedCall")
    
    if state == USSDMedicalInfo.VERIFY_PIN:
        session["pin"] = user_input
        session["patient_id"] = existing_user.id
        if not bcrypt.checkpw(
            session["pin"].encode("utf-8"),
            existing_user.pin.encode("utf-8")
        ):
            return end("PIN is incorrect. Try again!")
        session["state"] = USSDMedicalInfo.BLOOD_TYPE
        return con(f"Enter your blood type. Choose between {blood_type()}")
    
    if state == USSDMedicalInfo.BLOOD_TYPE:
        session["blood_type"] = user_input.upper()
        session["state"] = USSDMedicalInfo.ALLERGIES
        return con("List all allergies you might have")
    
    if state == USSDMedicalInfo.ALLERGIES:
        session["allergies"] = user_input.upper()
        session["state"] = USSDMedicalInfo.CHRONIC_ILLNESS
        return con("List all chronic diseases you might have")
    
    if state == USSDMedicalInfo.CHRONIC_ILLNESS:
        session["chronic_illness"] = user_input.upper()
        session["state"] = USSDMedicalInfo.RECENT_VACCINATION
        return con("List all recent vaccinations you might have taken")

    if state == USSDMedicalInfo.RECENT_VACCINATION:
        session["recent_vaccination"] = user_input.upper()
        
        medical_details = {
            "blood_type":session["blood_type"],
            "allergies":session["allergies"],
            "chronic_illness":session["chronic_illness"],
            "recent_vaccination":session["recent_vaccination"]

        }
        try:
            medical_data = medical_info_schema(**medical_details)
        except Exception as validation_error:
            return end("Incorrect data. Try again!")
        
        try:
            new_medical_data = PatientMedicalInfo(**medical_data.model_dump(mode="json"),
                                                  patient_id = session["patient_id"],
                                                  updated_at = datetime.utcnow()
                                                  )

            db.add(new_medical_data)
            db.commit()
            db.refresh(new_medical_data)
        except Exception as database_error:
            return end("An error happened! Try again!")
        
        return end(f"Medical data registered for patient {existing_user.first_name} {existing_user.last_name}")
