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
    1. sys._MEIPASS (PyInstaller onefile) — חייב להיות ראשון!
    2. ליד ה-exe (גרסת התקנה ו-Portable)
    3. בתוך _internal (PyInstaller onedir)
    4. תיקיית העבודה הנוכחית (fallback)
    """
    if getattr(sys, 'frozen', False):
        candidates = []

        # onefile: הקבצים נמצאים ב-_MEIPASS הזמני — חייב להיות ראשון!
        if hasattr(sys, '_MEIPASS'):
            candidates.append(os.path.join(sys._MEIPASS, "talmud.db"))

        # ליד ה-exe (onedir / installer)
        candidates.append(os.path.join(os.path.dirname(sys.executable), "talmud.db"))

        # _internal (PyInstaller onedir חדש)
        candidates.append(os.path.join(os.path.dirname(sys.executable), "_internal", "talmud.db"))

        for p in candidates:
            if os.path.isfile(p):
                return p
        return ""

    # מצב פיתוח
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "talmud.db")


def _open_db(db_path: str) -> sqlite3.Connection | None:
    """פותח חיבור לבסיס נתונים קיים בלבד — לא יוצר קובץ חדש."""
    if not db_path or not os.path.isfile(db_path):
        return None
    try:
        # uri=True + ?mode=ro מונע יצירת קובץ ריק אם הנתיך שגוי
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        return con
    except sqlite3.OperationalError:
        return None


def load_masechet_list(folder: str) -> list:
    global DB_PATH

    # סדר חיפוש:
    # 1. הנתיב שהועבר כארגומנט
    # 2. חיפוש אוטומטי (_find_db)
    candidates = [
        os.path.join(folder, "talmud.db"),
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
        rows = con.execute("SELECT id, num, name FROM masechtot ORDER BY num").fetchall()
    except sqlite3.DatabaseError:
        con.close()
        return []

    con.close()
    DB_PATH = db_path
    return [{'id': r[0], 'num': r[1], 'name': r[2]} for r in rows]


def fetch_masechet(ms_id: int) -> tuple:
    if not DB_PATH:
        return [], []
    con = _open_db(DB_PATH)
    if con is None:
        return [], []
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
    if not DB_PATH:
        return []
    con = _open_db(DB_PATH)
    if con is None:
        return []
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
    if not DB_PATH:
        return []
    con = _open_db(DB_PATH)
    if con is None:
        return []

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
        word_map: OrderedDict = OrderedDict()
        for sw_id, sec_label, wit_name, content in rows:
            if sw_id not in word_map:
                word_map[sw_id] = {'section': sec_label, 'witnesses': {}}
            word_map[sw_id]['witnesses'][wit_name] = content

        return list(word_map.values())

    con.close()
    return []


def search_word_in_shas(word: str) -> list:
    if not DB_PATH or not word:
        return []
    con = _open_db(DB_PATH)
    if con is None:
        return []
    rows = con.execute(
        "SELECT m.name, p.page_label, s.section_label "
        "FROM texts t "
        "JOIN witnesses w ON w.id = t.witness_id "
        "JOIN sections s ON s.id = t.section_id "
        "JOIN pages p ON p.id = s.page_id "
        "JOIN masechtot m ON m.id = p.masechet_id "
        "WHERE w.position = 0 "
        "AND ("
        "  (' ' || replace(replace(replace(t.content, '.', ''), ',', ''), ':', '') || ' ') LIKE (? || ' %') "
        "  OR (' ' || replace(replace(replace(t.content, '.', ''), ',', ''), ':', '') || ' ') LIKE ('% ' || ? || ' %') "
        "  OR (' ' || replace(replace(replace(t.content, '.', ''), ',', ''), ':', '') || ' ') LIKE ('% ' || ? || ' ') "
        ")",
        (word, word, word)
    ).fetchall()
    con.close()
    return [{'masechet': r[0], 'page': r[1], 'section': r[2]} for r in rows]


def fetch_manuscript_info(witness_name: str) -> dict | None:
    if not DB_PATH:
        return None
    con = _open_db(DB_PATH)
    if con is None:
        return None

    has_mi_table = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='manuscript_info'"
    ).fetchone()

    if not has_mi_table:
        con.close()
        return None

    row = con.execute(
        "SELECT title, description, link FROM manuscript_info WHERE witness_name=?",
        (witness_name,)
    ).fetchone()

    con.close()
    if not row:
        return None

    return {'title': row[0], 'description': row[1], 'link': row[2]}
