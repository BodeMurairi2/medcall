#!/usr/bin/env python3

from fastapi import APIRouter, Depends, Form
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from controllers.ussd.registration import register_patient_controller
from services.send_ussd import send_ussd
from database.session import get_db
from schemas.users import PatientRegistration

router = APIRouter(prefix="/ussd", tags=["USSD"])


# Trigger USSD (optional)
@router.post("/trigger-ussd")
async def trigger_ussd():
    send_ussd()
    return {"status": "USSD sent"}


# USSD Callback
@router.post("", response_class=PlainTextResponse)
async def ussd_callback(
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form(""),
    db: Session = Depends(get_db)
):
    """
    Multi-step USSD menu for MedCall
    """
    print(f"USSD POST received: session={sessionId}, phone={phoneNumber}, text='{text}'")

    # MAIN MENU
    if text == "":
        response = (
            "CON Welcome to MedCall\n"
            "1. Register as patient\n"
            "2. Complete Personal Information\n"
            "3. Complete Medical Information\n"
            "4. View Personal Information\n"
            "5. View Medical Information\n"
            "6. Consultation History\n"
            "7. Subscription\n"
            "8. Quit"
        )

    # REGISTRATION FLOW
    elif text.startswith("1"):
        parts = text.split("*")
        step = len(parts)

        if step == 1:
            response = "CON Enter your first name"
        elif step == 2:
            response = "CON Enter your last name"
        elif step == 3:
            response = "CON Enter your email address (or 'none')"
        elif step == 4:
            response = "CON Enter your unique PIN (numbers only)"
        elif step == 5:
            response = "CON Confirm your PIN"
        elif step == 6:
            # Final step: process registration
            try:
                first_name = parts[1]
                last_name = parts[2]
                email = parts[3] if parts[3].lower() != "none" else None
                pin = int(parts[4])
                confirm_pin = int(parts[5])

                if pin != confirm_pin:
                    response = "END PINs do not match. Please try again."
                else:
                    user_input = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "phone_number": phoneNumber,
                        "pin": pin,
                        "email_address": email
                    }
                    result = register_patient_controller(db, user_input)
                    response = f"END Registration successful. Welcome {result['first_name']}"

            except ValueError:
                response = "END PIN must be numeric. Registration failed."
            except Exception as e:
                print("Registration error:", e)
                response = "END Registration failed. Please try again later."

        else:
            response = "END Invalid input. Please try again."

    # PERSONAL INFORMATION
    elif text == "2":
        response = "END Personal information flow is coming soon."

    # MEDICAL INFORMATION
    elif text == "3":
        response = "END Medical information flow is coming soon."

    # VIEW PERSONAL INFORMATION
    elif text == "4":
        response = "END Viewing personal information is coming soon."

    # VIEW MEDICAL INFORMATION
    elif text == "5":
        response = "END Viewing medical information is coming soon."

    # CONSULTATION HISTORY
    elif text == "6":
        response = "END Consultation history is coming soon."

    # SUBSCRIPTION
    elif text == "7":
        response = "END Subscription options are coming soon."

    # QUIT
    elif text == "8":
        response = "END Thank you for using MedCall. Goodbye!"

    # INVALID OPTION
    else:
        response = "END Invalid option. Please try again."

    return PlainTextResponse(response)


# Optional API to register a patient via REST
@router.post("/registration", status_code=201)
async def register_patient(
    request: PatientRegistration, db: Session = Depends(get_db)
):
    """
    FastAPI route to register a patient via USSD or REST
    """
    user_input = request.model_dump()
    response = register_patient_controller(db, user_input)
    return response
