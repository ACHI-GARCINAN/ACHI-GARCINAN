import os
import sqlite3
import sys

DB_PATH = ''

def get_base_dir() -> str:
    # תיקון קריטי: תמיכה בתיקייה זמנית של PyInstaller (עבור גרסה ניידת) ובתיקיית ה-EXE (עבור התקנה)
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
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
    rows = con.execute("SELECT id, num, name FROM masechtot ORDER BY num").fetchall()
    con.close()
    return [{'id': r[0], 'num': r[1], 'name': r[2]} for r in rows]

def fetch_masechet(ms_id: int) -> tuple:
    """מחזיר (witnesses, pages) עבור מסכת נתונה. pages הן רשימת {'page', '_id'}."""
    con = sqlite3.connect(DB_PATH)
    witnesses = [r[0] for r in con.execute(
        "SELECT name FROM witnesses WHERE masechet_id=? ORDER BY position", (ms_id,)
    ).fetchall()]
    page_rows = con.execute(
        "SELECT id, page_label FROM pages WHERE masechet_id=? ORDER BY num", (ms_id,)
    ).fetchall()
    pages = [{'id': r[0], 'page': r[1]} for r in page_rows]
    con.close()
    return witnesses, pages

def fetch_page_content(page_id: int) -> list:
    """
    מחזיר תוכן של דף - רשימה של אובייקטים:
    {'section': 'label', 'witnesses': {'witness_name': 'text', ...}}
    """
    con = sqlite3.connect(DB_PATH)
    section_rows = con.execute(
        "SELECT id, section_label FROM sections WHERE page_id=? ORDER BY num", (page_id,)
    ).fetchall()
    
    sections = []
    for sec_id, sec_label in section_rows:
        texts = con.execute(
            "SELECT w.name, t.text "
            "FROM texts t "
            "JOIN witnesses w ON w.id = t.witness_id "
            "WHERE t.section_id=?", (sec_id,)
        ).fetchall()
        sections.append({'section': sec_label, 'witnesses': dict(texts)})
    con.close()
    return sections

def fetch_page_words(page_id: int) -> list:
    con = sqlite3.connect(DB_PATH)
    has_sw_table = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='sections_words'"
    ).fetchone()

    if has_sw_table:
        rows = con.execute(
            "SELECT sw.id, s.section_label, w.name, wd.word "
            "FROM sections_words sw "
            "JOIN sections s ON s.id = sw.section_id "
            "JOIN sections_words_texts swt ON swt.sections_word_id = sw.id "
            "JOIN witnesses w ON w.id = swt.witness_id "
            "JOIN words wd ON wd.id = swt.word_id "
            "WHERE sw.page_id = ? "
            "ORDER BY sw.id, w.position",
            (page_id,)
        ).fetchall()
        con.close()

        from collections import OrderedDict
        word_map = OrderedDict()
        for sw_id, sec_label, wit_name, word_text in rows:
            if sw_id not in word_map:
                word_map[sw_id] = {'section': sec_label, 'witnesses': {}}
            word_map[sw_id]['witnesses'][wit_name] = word_text
        
        return list(word_map.values())
    
    con.close()
    return []