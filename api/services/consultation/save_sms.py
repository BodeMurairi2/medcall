#!/usr/bin/env python3

import json
from datetime import datetime
from sqlalchemy.orm import Session
from models.database_models import ConsultationSMS, Consultation
from database.session import get_db

def save_consultation_sms(
    db:Session,
    consultation_id: int,
    message_type: str,
    content: str,
    sms_metadata: dict
):
    """Save a single SMS message to a consultation."""
    sms = ConsultationSMS(
        consultation_id=consultation_id,
        message_type=message_type,
        content=content,
        sms_metadata=json.dumps(sms_metadata) if sms_metadata else None,
        timestamp=datetime.utcnow()
    )
    try:
        db.add(sms)
        db.commit()
        db.refresh(sms)
        return sms
    except Exception as error:
        print(f"Error:\n{error}")
        return
