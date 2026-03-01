#!/usr/bin/env python3
import requests
from config.settings import africas_config

API_KEY = africas_config.get("AFRICAS_API_KEY")
USERNAME = africas_config.get("username")
SHORTCODE = africas_config.get("channels")  # Sandbox shortcode
PHONE_NUMBER = "250700000000"  # Can be any number in sandbox
MESSAGE = "Welcome to MedCall"

def send_ussd():
    url = "https://api.africastalking.com/version1/ussd/send"
    headers = {"Content-Type": "application/json", "apiKey": API_KEY}
    payload = {
        "username": USERNAME,
        "phoneNumber": PHONE_NUMBER,
        "shortCode": SHORTCODE,
        "message": MESSAGE,
        "clientCallbackURL": "https://unparched-morris-unfinishable.ngrok-free.dev/ussd"
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        print("USSD request sent successfully!")
        print(response.json())
    else:
        print("Failed to send USSD request")
        print(response.text)