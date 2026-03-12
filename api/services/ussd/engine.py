#!/usr/bin/env python3

from services.ussd.session import get_session, save_session
from services.ussd.state import USSDState
from services.ussd.flows.menu_flow import main_menu
from services.ussd.flows.registration_flow import registration_flow
from services.ussd.response import end
from sqlalchemy.orm import Session

def extract_input(text: str):

    if text == "":
        return ""

    return text.split("*")[-1]


def ussd_engine(session_id, text, phone_number, db:Session):

    session = get_session(session_id)

    if not session:

        session = {
            "phone": phone_number,
            "state": USSDState.MAIN_MENU
        }

        save_session(session_id, session)

        return main_menu(session)

    state = session["state"]

    # MAIN MENU INPUT
    if state == USSDState.MAIN_MENU:

        if text == "1":

            session["state"] = USSDState.REGISTER_FIRST_NAME
            return "CON Enter your first name"

        if text == "8":

            return end("Thank you for using MedCall")

    # REGISTRATION FLOW
    if state.name.startswith("REGISTER"):
        user_input = extract_input(text=text)
        return registration_flow(session, user_input, db=db)

    return end("Invalid input")
