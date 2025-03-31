# utils/validators.py
import re
import datetime

def is_valid_full_name(name: str) -> bool:
    """Check if the name contains only Russian letters and at least two words."""
    # Disallow English letters by checking for their presence
    if re.search(r'[A-Za-z]', name):
        return False
    # Require at least two words (split by whitespace)
    parts = [p for p in name.split() if p]
    return len(parts) >= 2

def normalize_name(name: str) -> str:
    """Normalize the name: convert to lowercase and replace 'ё' with 'е'."""
    name_lower = name.strip().lower()
    return name_lower.replace('ё', 'е')

months = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}

def format_datetime(date_str):
    if date_str != 'не указано':
        dt = datetime.datetime.fromisoformat(date_str)
        # Форматируем как "22 апреля 15:30"
        return f"{dt.day} {months[dt.month - 1]} {dt.strftime('%H:%M')}"
    return date_str