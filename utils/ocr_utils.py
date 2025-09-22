import re

def clean_plate_text(text):
    """Clean OCR text: keep only alphanumeric, uppercase"""
    return re.sub(r'[^A-Z0-9]', '', text.upper())