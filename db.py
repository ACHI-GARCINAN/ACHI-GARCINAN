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
