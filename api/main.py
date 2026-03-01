#!/usr/bin/env python3
import uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
from services.send_ussd import send_ussd  # your USSD sender

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to MedCall"}

# Route to trigger USSD (initiates session)
@app.post("/trigger-ussd")
async def trigger_ussd():
    send_ussd()
    return {"status": "USSD sent"}

# USSD callback route — Africa's Talking will POST here
@app.post("/ussd", response_class=PlainTextResponse)
async def ussd_callback(
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form("")
):
    """
    Multi-step USSD menu for MedCall
    """
    print(f"USSD POST received: session={sessionId}, phone={phoneNumber}, text='{text}'")
    # Initial menu
    if text == "":
        response = "CON Welcome to MedCall\n"
        response += "1. Find a doctor\n"
        response += "2. Emergency"
    
    # Option 1 → Choose type of doctor
    elif text == "1":
        response = "CON Select doctor type:\n"
        response += "1. General Practitioner\n"
        response += "2. Specialist"

    elif text == "1*1":
        response = "END Searching for General Practitioner near you..."

    elif text == "1*2":
        response = "END Searching for Specialists near you..."

    # Option 2 → Emergency
    elif text == "2":
        response = "END Connecting to emergency services..."

    # Catch-all
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
