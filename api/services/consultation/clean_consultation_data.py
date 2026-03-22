#!/usr/bin/env python3

import json
from typing import List, Dict, Union

def parse_json(raw_content: list) -> List[Dict]:
    """
    This function turns a raw message to a well-formatted JSON response
    as Python dicts, not strings.
    """
    clean_message = []
    for message in raw_content:
        cleaned = message["text"].replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned)
        clean_message.append(parsed)
    return clean_message
