"""
מנהל הגדרות - שומר ומשחזר הגדרות גופן וערכת נושא בין הפעלות
"""
import json
import os
import sys


def get_settings_path() -> str:
    """מחזיר נתיב לקובץ הגדרות."""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'settings.json')

DEFAULTS = {
    'font_family': 'David',
    'font_size': 16,
    'theme': 'classic',
    'highlight_diffs': False,
    'hide_empty_witnesses': True,
}


def load_settings() -> dict:
    path = get_settings_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # merge with defaults to handle missing keys
            result = dict(DEFAULTS)
            result.update(data)
            return result
        except Exception:
            pass
    return dict(DEFAULTS)


def save_settings(settings: dict) -> None:
    path = get_settings_path()
    try:
        # Load existing settings first to preserve other keys
        current = load_settings()
        current.update(settings)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
