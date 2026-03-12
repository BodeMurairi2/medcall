#!/usr/bin/env python3

from services.ussd.response import con
from services.ussd.state import USSDState

def main_menu(session):

    session["state"] = USSDState.MAIN_MENU

    return con(
        "Welcome to MedCall\n"
        "1. Register as patient\n"
        "2. Personal Information\n"
        "3. Medical Information\n"
        "8. Quit"
    )
