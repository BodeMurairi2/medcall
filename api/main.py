#!/usr/bin/env python3
import uvicorn
from fastapi import FastAPI, Form, Depends
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from services.send_ussd import send_ussd
from routes.ussd.registration import router as registration_router
from database import get_db

app = FastAPI(title="MedCall USSD Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(registration_router)

@app.get("/")
async def root():
    return {"message": "Welcome to MedCall"}

@app.post("/trigger-ussd")
async def trigger_ussd():
    send_ussd()
    return {"status": "USSD sent"}

@app.post("/ussd", response_class=PlainTextResponse)
async def ussd_callback(
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form(""),
    db: Session = Depends(get_db)
):
    """
    Multi-step USSD menu for MedCall
    Integrates registration and other flows
    """
    print(f"USSD POST received: session={sessionId}, phone={phoneNumber}, text='{text}'")

    if text == "":
        response = "CON Welcome to MedCall\n"
        response += "1. Register as patient\n"
        response += "2. Find a doctor\n"
        response += "3. Emergency"

    elif text == "1":
        response = "CON Enter your first name:"

    elif text.startswith("1*"):
        try:
            # Split user input by *
            parts = text.split("*")[1:]  # remove initial "1"
            if len(parts) < 4:
                response = "CON Please provide all details as: first_name*last_name*pin*email"
            else:
                first_name, last_name, pin, email = parts
                # Convert PIN to int
                pin = int(pin)

                # Call registration controller directly
                from controller.registration import register_patient_controller
                user_input = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone_number": phoneNumber,
                    "pin": pin,
                    "email_address": email if email != "none" else None
                }
                result = register_patient_controller(db, user_input)
                response = f"END Registration successful! Welcome {result['first_name']}"

        except ValueError as ve:
            response = f"END Error: {str(ve)}"
        except Exception as e:
            response = f"END Registration failed: {str(e)}"

    # Option 2 → Find doctor
    elif text == "2":
        response = "CON Select doctor type:\n"
        response += "1. General Practitioner\n"
        response += "2. Specialist"

    elif text == "2*1":
        response = "END Searching for General Practitioner near you..."

    elif text == "2*2":
        response = "END Searching for Specialists near you..."

    elif text == "3":
        response = "END Connecting to emergency services..."

    else:
        response = "END Invalid option. Please try again."

    return response

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )