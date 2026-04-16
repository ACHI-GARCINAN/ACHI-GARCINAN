import re
import difflib


def tokenize(text: str) -> list:
    return re.split(r'(\s+)', text)


def normalize_word(w: str) -> str:
    w = re.sub(r'[\u05B0-\u05C7]', '', w)
    w = re.sub(r'[\u05f3\u05f4",.\-:;!?()\[\]]', '', w)
    return w.strip()


def _diff_highlight(source_text: str, reference_text: str, highlight_style: str) -> str:
    """
    מחזיר HTML עם הדגשה של מילים בטקסט המקור שאינן תואמות לרצף בטקסט הייחוס.
    משתמש ב-difflib.SequenceMatcher כדי להשוות לפי סדר ותדירות, לא רק לפי הימצאות.
    """
    source_tokens = tokenize(source_text)
    ref_tokens = tokenize(reference_text)

    source_words = [normalize_word(t) for t in source_tokens if t.strip()]
    ref_words    = [normalize_word(t) for t in ref_tokens    if t.strip()]

    matched = [False] * len(source_words)
    matcher = difflib.SequenceMatcher(None, source_words, ref_words, autojunk=False)
    for a, b, size in matcher.get_matching_blocks():
        for i in range(size):
            matched[a + i] = True

    parts = []
    word_idx = 0
    for token in source_tokens:
        if not token.strip():
            parts.append(token.replace('\n', '<br>'))
        else:
            norm = normalize_word(token)
            if norm and not matched[word_idx]:
                parts.append(f'<span style="{highlight_style}">{token}</span>')
            else:
                parts.append(token)
            word_idx += 1

    return ''.join(parts)


def build_highlighted_html(witness_text: str, base_text: str) -> str:
    """מדגיש מילים בעד הנוסח שאינן מופיעות ברצף המתאים בטקסט הבסיס (וילנא)."""
    style = "background-color:#FFD700;color:#1A202C;border-radius:3px;padding:0 2px;font-weight:bold;"
    return _diff_highlight(witness_text, base_text, style)


def build_vilna_diff_html(base_text: str, witness_text: str) -> str:
    """מדגיש מילים בטקסט וילנא שאינן מופיעות ברצף המתאים בעד הנוסח."""
    style = "background-color:#E53E3E;color:#FFFFFF;border-radius:3px;padding:0 2px;font-weight:bold;"
    return _diff_highlight(base_text, witness_text, style)


# ── גימטריה ──────────────────────────────────────────────────
_HEB_VALS = {
    'א': 1,  'ב': 2,  'ג': 3,  'ד': 4,  'ה': 5,
    'ו': 6,  'ז': 7,  'ח': 8,  'ט': 9,  'י': 10,
    'כ': 20, 'ך': 20, 'ל': 30, 'מ': 40, 'ם': 40,
    'נ': 50, 'ן': 50, 'ס': 60, 'ע': 70, 'פ': 80,
    'ף': 80, 'צ': 90, 'ץ': 90, 'ק': 100, 'ר': 200,
    'ש': 300, 'ת': 400,
}


def _heb_to_int(s: str) -> int:
    s = re.sub(r'["\u05f4\u05f3\u2019\u2018\'\u05f3]', '', s).strip()
    if not s:
        return 0
    total = 0
    for ch in s:
        v = _HEB_VALS.get(ch, 0)
        if v == 0:
            return 0
        total += v
    return total


def _normalize_page(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r'^\u05d3\u05e3\s*', '', raw).strip()
    raw = re.sub(r'["\u05f4\u05f3\u2019\u2018\'\u05f3]', '', raw).strip()
    return raw


def _page_matches(page_str: str, query_page: str) -> bool:
    norm_data  = _normalize_page(page_str)
    norm_query = _normalize_page(query_page)
    if norm_data == norm_query:
        return True
    val_data  = _heb_to_int(norm_data)
    val_query = _heb_to_int(norm_query)
    if val_data and val_query and val_data == val_query:
        return True
    try:
        if norm_query.isdigit() and val_data == int(norm_query):
            return True
    except ValueError:
        pass
    return False


def _masechet_matches(ms_name: str, query_name: str) -> bool:
    name_clean = re.sub(r'^\u05de\u05e1\u05db\u05ea\s*', '', ms_name).strip()
    q = query_name.strip()
    return name_clean == q or name_clean.startswith(q) or q.startswith(name_clean)
