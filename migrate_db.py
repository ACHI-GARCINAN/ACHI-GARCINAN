"""
migrate_db.py — ממיר talmud.db לפורמט מקוצר.
שימוש: python migrate_db.py input.db output.db
"""
import sqlite3, shutil, sys, os

def migrate(src: str, dst: str):
    if os.path.exists(dst):
        os.remove(dst)
    shutil.copy2(src, dst)
    con = sqlite3.connect(dst)
    con.execute("PRAGMA foreign_keys=OFF")

    print("יוצר טבלת מילים...")
    con.execute("CREATE TABLE words (id INTEGER PRIMARY KEY AUTOINCREMENT, word TEXT NOT NULL UNIQUE)")
    con.execute("INSERT OR IGNORE INTO words(word) SELECT DISTINCT content FROM sections_words_texts WHERE content IS NOT NULL")
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    print(f"  {n:,} מילים ייחודיות")

    print("בונה sections_words_texts חדשה (ללא NULL, word_id)...")
    con.execute("""
        CREATE TABLE sections_words_texts_new (
            id               INTEGER PRIMARY KEY,
            sections_word_id INTEGER NOT NULL,
            witness_id       INTEGER NOT NULL,
            word_id          INTEGER NOT NULL REFERENCES words(id)
        )
    """)
    con.execute("""
        INSERT INTO sections_words_texts_new(id, sections_word_id, witness_id, word_id)
        SELECT swt.id, swt.sections_word_id, swt.witness_id, w.id
        FROM sections_words_texts swt
        JOIN words w ON w.word = swt.content
        WHERE swt.content IS NOT NULL
    """)
    con.commit()

    print("בונה sections_words חדשה (section_id במקום section_label)...")
    con.execute("""
        CREATE TABLE sections_words_new (
            id         INTEGER PRIMARY KEY,
            section_id INTEGER NOT NULL REFERENCES sections(id),
            page_id    INTEGER NOT NULL REFERENCES pages(id)
        )
    """)
    con.execute("""
        INSERT INTO sections_words_new(id, section_id, page_id)
        SELECT sw.id,
               (SELECT s.id FROM sections s WHERE s.page_id = sw.page_id AND s.section_label = sw.section_label),
               sw.page_id
        FROM sections_words sw
    """)
    nulls = con.execute("SELECT COUNT(*) FROM sections_words_new WHERE section_id IS NULL").fetchone()[0]
    if nulls:
        print(f"  אזהרה: {nulls} שורות ללא section_id")
    con.commit()

    print("מחליף טבלאות...")
    con.execute("DROP TABLE sections_words_texts")
    con.execute("ALTER TABLE sections_words_texts_new RENAME TO sections_words_texts")
    con.execute("DROP TABLE sections_words")
    con.execute("ALTER TABLE sections_words_new RENAME TO sections_words")
    con.commit()

    print("מעדכן אינדקסים...")
    for idx in ["idx_witnesses_masechet","idx_pages_masechet","idx_sections_page",
                "idx_texts_section","idx_texts_witness","idx_sections_words_page",
                "idx_sections_words_texts_word","idx_sections_words_texts_witness"]:
        con.execute(f"DROP INDEX IF EXISTS {idx}")
    con.execute("CREATE INDEX idx_witnesses_masechet ON witnesses(masechet_id)")
    con.execute("CREATE INDEX idx_pages_masechet     ON pages(masechet_id)")
    con.execute("CREATE INDEX idx_sections_page      ON sections(page_id)")
    con.execute("CREATE INDEX idx_texts_section      ON texts(section_id)")
    con.execute("CREATE INDEX idx_texts_witness      ON texts(witness_id)")
    con.execute("CREATE INDEX idx_sw_section         ON sections_words(section_id)")
    con.execute("CREATE INDEX idx_sw_page            ON sections_words(page_id)")
    con.execute("CREATE INDEX idx_swt_word           ON sections_words_texts(sections_word_id)")
    con.execute("CREATE INDEX idx_swt_witness        ON sections_words_texts(witness_id)")
    con.execute("CREATE INDEX idx_words_word         ON words(word)")
    con.commit()
    con.close()

    print("VACUUM...")
    con2 = sqlite3.connect(dst)
    con2.execute("VACUUM")
    con2.close()

    old = os.path.getsize(src)
    new = os.path.getsize(dst)
    print(f"\nגודל ישן:  {old/1024/1024:.1f} MB")
    print(f"גודל חדש:  {new/1024/1024:.1f} MB")
    print(f"חסכון:     {(old-new)/1024/1024:.1f} MB  ({(old-new)/old*100:.0f}%)")
    print("✓ הושלם")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("שימוש: python migrate_db.py input.db output.db")
        sys.exit(1)
    migrate(sys.argv[1], sys.argv[2])
