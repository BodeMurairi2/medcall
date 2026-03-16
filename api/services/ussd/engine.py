#!/usr/bin/env python3

from services.ussd.session import get_session, save_session
from services.ussd.state import USSDState
from services.ussd.state import USSDPersonalInfo
from services.ussd.state import USSDMedicalInfo
from services.ussd.flows.menu_flow import main_menu
from services.ussd.flows.registration_flow import registration_flow
from services.ussd.flows.medical_info import save_medical_info
from services.ussd.flows.complete_personal_infoflow import complete_personal_info_flow

from services.ussd.response import end
from sqlalchemy.orm import Session

def extract_input(text: str):

    if text == "":
        return ""

    return text.split("*")[-1]

def ussd_engine(session_id, text, phone_number, db: Session):

    session = get_session(session_id)

    if not session:
        session = {
            "phone": phone_number,
            "state": USSDState.MAIN_MENU
        }

    state = session["state"]

    if state == USSDState.MAIN_MENU:

        if text == "" or text is None:
            response = main_menu(session)

        elif text == "1":
            session["state"] = USSDState.REGISTER_FIRST_NAME
            response = "CON Enter your first name"

        elif text == "2":
            session["state"] = USSDPersonalInfo.VERIFY_PIN
            response = "CON Enter your PIN"

        elif text == "3":
            session["state"] = USSDMedicalInfo.VERIFY_PIN
            response = "CON Enter your PIN"

        elif text == "4":
            response = end("View personal information coming up soon...")
        elif text == "5":
            response = end("View medical information coming up soon...")
        elif text == "6":
            response = end("View consultation information coming up soon...")
        elif text == "7":
            response = end("Subscription coming up soon...")
        elif text == "8":
            response = end("Thank you for using MedCall")

        else:
            response = end("Invalid Input")

        save_session(session_id, session)
        return response

    user_input = extract_input(text)

    if state.name.startswith("REGISTER"):
        response = registration_flow(session, user_input, db=db)

    elif isinstance(state, USSDPersonalInfo):
        response = complete_personal_info_flow(session, user_input, db=db)
    elif isinstance(state, USSDMedicalInfo):
        response = save_medical_info(session, user_input, db)
    else:
        response = end("Invalid input")

    save_session(session_id, session)
    return response
