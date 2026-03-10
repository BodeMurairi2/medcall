#!/usr/bin/env python3

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from controller.registration import register_patient_controller
from database import get_db
from schemas.users import PatientRegistration

router = APIRouter(prefix="/registration", tags=["Registration"])

@router.post("/ussd", status_code=201)
def register_patient(request: PatientRegistration, db: Session = Depends(get_db)):
    """
    FastAPI route to register a patient via USSD.
    """
    user_input = request.model_dump()

    response = register_patient_controller(db, user_input)
    return response