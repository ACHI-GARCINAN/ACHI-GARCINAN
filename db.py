import os
import sqlite3
import sys

DB_PATH = ''


def get_base_dir() -> str:
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
        "SELECT id, page_label FROM pages WHERE masechet_id=? ORDER BY id", (ms_id,)
    ).fetchall()
    con.close()
    pages = [{'page': r[1], '_id': r[0]} for r in page_rows]
    return witnesses, pages


def fetch_page(page_id: int) -> list:
    """מחזיר רשימת קטעים עם עדי נוסח עבור דף נתון."""
    con = sqlite3.connect(DB_PATH)
    sections_raw = con.execute(
        "SELECT id, section_label FROM sections WHERE page_id=? ORDER BY id",
        (page_id,)
    ).fetchall()
    sections = []
    for sec_id, sec_label in sections_raw:
        texts = con.execute(
            "SELECT w.name, t.content FROM texts t "
            "JOIN witnesses w ON w.id = t.witness_id "
            "WHERE t.section_id=?", (sec_id,)
        ).fetchall()
        sections.append({'section': sec_label, 'witnesses': dict(texts)})
    con.close()
    return sections


def fetch_page_words(page_id: int) -> list:
    """
    מחזיר רשימת מילים עבור דף נתון — כל פריט הוא dict עם 'section' ו-'witnesses'.
    שולף מטבלת sections_words / sections_words_texts (המקבילה ל-sections_words ב-JSON).
    """
    con = sqlite3.connect(DB_PATH)

    # בדוק אם קיימת טבלת sections_words
    has_sw_table = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='sections_words'"
    ).fetchone()

    if has_sw_table:
        # שלוף את כל השורות של הדף בשאילתה אחת, ממוינות לפי סדר המילה ואחר-כך עד הנוסח
        rows = con.execute(
            "SELECT sw.id, sw.section_label, w.name, swt.content "
            "FROM sections_words sw "
            "JOIN sections_words_texts swt ON swt.sections_word_id = sw.id "
            "JOIN witnesses w ON w.id = swt.witness_id "
            "WHERE sw.page_id = ? "
            "ORDER BY sw.id, w.position",
            (page_id,)
        ).fetchall()
        con.close()

        # קיבוץ לפי מזהה מילה (sw.id) תוך שמירת הסדר
        from collections import OrderedDict
        word_map: OrderedDict = OrderedDict()
        for sw_id, sec_label, wit_name, content in rows:
            if sw_id not in word_map:
                word_map[sw_id] = {'section': sec_label, 'witnesses': {}}
            word_map[sw_id]['witnesses'][wit_name] = content

        return list(word_map.values())

    con.close()
    return []
