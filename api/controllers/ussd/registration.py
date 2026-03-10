#!/usr/bin/env python3

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from services.registration_service import ussd_register_patient_basic
from models import PatientRegistration

def register_patient_controller(session: Session, user_input: dict) -> dict:
    """
    Controller for registering a patient via USSD.
    Handles errors and calls the service function.
    """
    try:
        patient = ussd_register_patient_basic(session, user_input)
        return patient

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(error)}"
        )
