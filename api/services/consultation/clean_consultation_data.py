#!/usr/bin/env python3

import json

def clean_raw_data(raw_content):
    """clean raw consultation data"""
    return raw_content.replace("```json", "").replace("```", "").strip()

def parse_json(cleaned):
    """parse to json raw data"""
    try:
        parsed = json.loads(cleaned)
        return json.dumps(parsed, indent=2)
    except Exception as error:
        raise f"\n Failed to parse JSON\n: {error}"
