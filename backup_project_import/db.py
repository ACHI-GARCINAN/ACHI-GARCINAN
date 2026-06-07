import os
import sqlite3
import sys

DB_PATH = ''

def get_base_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def _find_db() -> str:
    """
    מחפש את talmud.db בסדר עדיפויות:
    1. sys._MEIPASS (PyInstaller onefile)
    2. ליד ה-exe (גרסת התקנה)
    3. בתוך _internal (PyInstaller onedir)
    4. בתוך תיקיית project (מיקום ה-Build הנוכחי)
    """
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        candidates = []

        if hasattr(sys, '_MEIPASS'):
            candidates.append(os.path.join(sys._MEIPASS, "talmud.db"))
        
        candidates.append(os.path.join(exe_dir, "talmud.db"))
        candidates.append(os.path.join(exe_dir, "_internal", "talmud.db"))
        candidates.append(os.path.join(exe_dir, "project", "talmud.db"))

        for p in candidates:
            if os.path.isfile(p):
                return p
        return ""

    # מצב פיתוח
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "project", "talmud.db")

def _open_db(db_path: str) -> sqlite3.Connection | None:
    """פותח חיבור לבסיס נתונים קיים בלבד — לא יוצר קובץ חדש."""
    if not db_path or not os.path.isfile(db_path):
        return None
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        return con
    except sqlite3.OperationalError:
        return None

def load_masechet_list(folder: str) -> list:
    global DB_PATH
    candidates = [
        os.path.join(folder, "talmud.db"),
        os.path.join(folder, "project", "talmud.db")
    ]

    auto = _find_db()
    if auto:
        candidates.append(auto)

    db_path = ""
    for p in candidates:
        if os.path.isfile(p):
            db_path = p
            break

    if not db_path:
        return []

    con = _open_db(db_path)
    if con is None:
        return []

    try:
        rows = con.execute("SELECT id, num, name FROM masechtot").fetchall()
        con.close()
        return rows
    except Exception:
        return []