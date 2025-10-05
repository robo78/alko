import json
import os

SETTINGS_FILE = 'settings.json'

DEFAULT_SETTINGS = {
    "smtp_server": "",
    "smtp_port": 587,
    "smtp_user": "",
    "smtp_password": "",
    "recipient_email": "",
    "reminders_enabled": False,
    "reminder_time": "20:00",
    "font_size": 12,
}

def load_settings():
    """Loads settings from the JSON file. Returns default settings if the file doesn't exist."""
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4)
        return DEFAULT_SETTINGS
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            # Ensure all default keys exist
            for key, value in DEFAULT_SETTINGS.items():
                settings.setdefault(key, value)
            return settings
    except (json.JSONDecodeError, IOError):
        return DEFAULT_SETTINGS

def save_settings(settings):
    """Saves the given settings to the JSON file."""
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)
