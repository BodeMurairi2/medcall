#!/usr/bin/env python3
import bcrypt
from sqlalchemy.orm import Session
from models.database_models import PatientRegistration
from schemas.users import PatientRegistration as registration_schema
from datetime import datetime

def ussd_register_patient_basic(session: Session, user_input: dict) -> dict:
    """
    Registers a patient via USSD.
    The PIN is provided as an integer by the user but stored hashed.

    user_input: {
        "first_name": str,
        "last_name": str,
        "phone_number": str,
        "pin": int,
        "email_address": Optional[str]
    }
    """

    existing_patient = session.query(PatientRegistration).filter_by(
        phone_number=user_input["phone_number"]
    ).first()
    
    if existing_patient:
        raise ValueError("This phone number is already registered.")

    pin_str = str(user_input["pin"])
    salt = bcrypt.gensalt()
    hashed_pin = bcrypt.hashpw(pin_str.encode("utf-8"), salt).decode("utf-8")

    new_user = registration_schema(
        first_name=user_input["first_name"],
        last_name=user_input["last_name"],
        phone_number=user_input["phone_number"],
        pin=user_input["pin"],
        email_address=user_input.get("email_address")
    )

    user_dict = new_user.model_dump()

    user_dict["pin"] = hashed_pin

    # Create SQLAlchemy instance
    patient = PatientRegistration(
        **user_dict,
        updated_at=datetime.utcnow()
    )

    session.add(patient)
    session.commit()
    session.refresh(patient)

    return {
        "message": "Success",
        "patient_id": patient.patient_id,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "phone_number": patient.phone_number,
        "email_address": patient.email_address
    }
