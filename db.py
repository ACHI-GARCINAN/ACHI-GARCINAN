import os
import sqlite3
import sys

DB_PATH = ''

def get_base_dir() -> str:
    if getattr(sys, 'frozen', False):
        # השינוי הנדרש: תמיכה בנתיב הפנימי של PyInstaller
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

def load_masechet_list(folder: str) -> list:
    global DB_PATH
    db_path = os.path.join(folder, "talmud.db")
    if not os.path.exists(db_path):
        db_path = os.path.join(get_base_dir(), "talmud.db")
    if not os.path.exists(db_path):
        return []
    DB_PATH = db_path
    con = sqlite3.connect(db_path)
    rows = con.execute("SELECT id, num, name FROM mase