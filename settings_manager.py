"""
מנהל הגדרות - שומר ומשחזר הגדרות גופן וערכת נושא בין הפעלות
"""
import json
import os
import sys


def get_settings_path() -> str:
    """
    מחזיר נתיב לקובץ הגדרות בתיקיית AppData של המשתמש.
    יוצר תיקייה ייעודית אם היא אינה קיימת.
    """
    # איתור תיקיית AppData המערכתית
    app_data = os.environ.get('APPDATA')
    
    # הגדרת נתיב התיקייה עבור התוכנה
    base_dir = os.path.join(app_data, 'נוסחאות התלמוד')
    
    # יצירת התיקייה במידה ואינה קיימת
    if not os.path.exists(base_dir):
        try:
            os.makedirs(base_dir)
        except Exception:
            # גיבוי למקרה של תקלה: שימוש בנתיב הרגיל ליד הקובץ
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                
    return os.path.join(base_dir, 'settings.json')

DEFAULTS = {
    'font_family': 'David',
    'font_size': 16,
    'theme': 'classic',
    'highlight_diffs': False,
    'hide_empty_witnesses': True,
    'hide_minor_diffs': False,
    'continuous_sections_view': False,
    'display_mode': 'sections',
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


def save_last_position(masechet_idx: int, page_idx: int) -> None:
    """שומר את המיקום האחרון של המשתמש (מסכת ודף)."""
    save_settings({'last_masechet_idx': masechet_idx, 'last_page_idx': page_idx})


def load_last_position() -> tuple:
    """טוען את המיקום האחרון. מחזיר (masechet_idx, page_idx) או (0, 0) כברירת מחדל."""
    settings = load_settings()
    return (
        settings.get('last_masechet_idx', 0),
        settings.get('last_page_idx', 0),
    )


def save_layout(splitter_sizes: list, sidebar_visible: bool) -> None:
    """שומר את מצב הפריסה (splitter + sidebar)."""
    save_settings({
        'splitter_sizes': splitter_sizes,
        'sidebar_visible': sidebar_visible,
    })


def load_layout() -> dict:
    """טוען את מצב הפריסה. מחזיר ברירות מחדל אם לא נשמר."""
    s = load_settings()
    return {
        'splitter_sizes': s.get('splitter_sizes', [215, 780, 420]),
        'sidebar_visible': s.get('sidebar_visible', True),
    }
