import re
import difflib


def tokenize(text: str) -> list:
    return re.split(r'(\s+)', text)


def normalize_word(w: str) -> str:
    w = re.sub(r'[\u05B0-\u05C7]', '', w)
    w = re.sub(r'[\u05f3\u05f4",.\-:;!?()\[\]]', '', w)
    return w.strip()


def is_minor_diff(source_word: str, ref_word: str) -> bool:
    """
    בודק אם ההבדל בין שתי מילים הוא "שינוי קל" לפי הכללים:
    1. אותה מילה ורק חסר אותיות ויש גרש (') במילה המקורית.
    2. אותה מילה וחסר רק י', אפילו בלי גרש.
    חריג: אליעזר ואלעזר נחשבים כשינוי משמעותי (לא קל).
    """
    s = normalize_word(source_word)
    r = normalize_word(ref_word)
    if not s or not r:
        return False
    if s == r:
        return True

    # חריג: אליעזר vs אלעזר — תמיד ייחשב כשינוי משמעותי
    _ELIEZER_FORMS = {'אליעזר', 'אלעזר'}
    if s in _ELIEZER_FORMS and r in _ELIEZER_FORMS and s != r:
        return False

    # הסרת גרשים לצורך השוואה
    s_no_quotes = s.replace("'", "").replace('"', '')
    r_no_quotes = r.replace("'", "").replace('"', '')

    # כלל 2: חסר רק י' (אפילו בלי גרש)
    if s_no_quotes.replace('י', '') == r_no_quotes.replace('י', ''):
        return True

    # כלל 1: חסר אותיות ויש גרש במקור
    # אם המילה המקורית מכילה גרש והיא מוכלת במילת הייחוס (או להיפך אחרי ניקוי גרשים)
    if "'" in source_word or '"' in source_word:
        if s_no_quotes in r_no_quotes or r_no_quotes in s_no_quotes:
            return True

    return False



# ── ראשי תיבות ──────────────────────────────────────────────────

_GERSHAYIM = '״'  # ״

def _get_heb_letters(w: str) -> str:
    """מחזיר רק אותיות עבריות, ללא ניקוד ופיסוק."""
    w = re.sub(r'[ְ-ׇ]', '', w)
    return re.sub(r'[^א-ת]', '', w)

def _has_gershayim(w: str) -> bool:
    """בודק אם מילה מכילה גרשיים (") — סימן ראשי תיבות."""
    return '"' in w or _GERSHAYIM in w

def _acronym_matches_words(acronym_word: str, full_words: list) -> bool:
    """
    בודק אם acronym_word (עם גרשיים) הוא ראשי תיבות של full_words.
    כל אות בר"ת יכולה להתאים לאות הבאה (לאו דווקא הראשונה) של כל מילה,
    כך שכנה"ג מתאים ל-כנסת הגדולה ומנ"ל ל-מנא ליה.
    ו' חיבור: יכולה לדלג ללא צריכת אות/מילה.
    """
    if not _has_gershayim(acronym_word):
        return False
    letters = _get_heb_letters(acronym_word)
    if len(letters) < 2 or not full_words:
        return False

    full_letters = [_get_heb_letters(w) for w in full_words]

    def match(li: int, wi: int, ci: int) -> bool:
        """
        li = אינדקס באותיות הר"ת
        wi = אינדקס במילה הנוכחית ב-full_words
        ci = אינדקס האות הנוכחית בתוך full_words[wi]
        """
        if li == len(letters):
            return True
        if wi >= len(full_words):
            return False
        letter = letters[li]
        word_ltrs = full_letters[wi] if wi < len(full_letters) else ''
        # ו\'\' חיבור: דלג עליה ללא צריכת אות
        if letter == 'ו' and match(li + 1, wi, ci):
            return True
        # האות תואמת לאות הנוכחית במילה
        if ci < len(word_ltrs) and word_ltrs[ci] == letter:
            if match(li + 1, wi, ci + 1):   # המשך באותה מילה
                return True
            if match(li + 1, wi + 1, 0):    # מעבר למילה הבאה
                return True
        # דלג למילה הבאה (רק אם כבר התחלנו לצרוך אותיות ממילה זו)
        if ci > 0 and match(li, wi + 1, 0):
            return True
        return False

    return match(0, 0, 0)

def is_acronym_minor_diff(src_slice: list, ref_slice: list) -> bool:
    """
    בודק אם ההחלפה src_slice↔ref_slice היא שינוי קל של ראשי תיבות (דו-כיווני).
    כיוון 1: src הוא ר"ת ו-ref הן המילים השלמות (replace 1→N).
    כיוון 2: ref הוא ר"ת ו-src הן המילים השלמות (replace N→1).
    כיוון 3: 1→1 כשאחת מהן היא ר"ת של השנייה (נדיר אבל אפשרי).
    """
    if len(src_slice) == 1 and len(ref_slice) >= 2:
        return _acronym_matches_words(src_slice[0], ref_slice)
    if len(ref_slice) == 1 and len(src_slice) >= 2:
        return _acronym_matches_words(ref_slice[0], src_slice)
    if len(src_slice) == 1 and len(ref_slice) == 1:
        return (_acronym_matches_words(src_slice[0], ref_slice) or
                _acronym_matches_words(ref_slice[0], src_slice))
    return False


def _diff_highlight(source_text: str, reference_text: str, highlight_style: str, hide_minor: bool = False) -> str:
    """
    מחזיר HTML עם הדגשה של מילים בטקסט המקור שאינן תואמות לרצף בטקסט הייחוס.
    משתמש ב-difflib.SequenceMatcher כדי להשוות לפי סדר ותדירות, לא רק לפי הימצאות.
    """
    source_tokens = tokenize(source_text)
    ref_tokens = tokenize(reference_text)

    # שמור מילים מקוריות (לצורך זיהוי גרשיים בר"ת) ומנורמלות (להשוואה)
    source_words_orig = [t for t in source_tokens if t.strip()]
    ref_words_orig    = [t for t in ref_tokens    if t.strip()]
    source_words = [normalize_word(t) for t in source_words_orig]
    ref_words    = [normalize_word(t) for t in ref_words_orig]

    matched = [False] * len(source_words)
    matcher = difflib.SequenceMatcher(None, source_words, ref_words, autojunk=False)
    for a, b, size in matcher.get_matching_blocks():
        for i in range(size):
            matched[a + i] = True

    # אם hide_minor מופעל, נסמן כ"תואמים" גם מילים שהן שינוי קל
    if hide_minor:
        # נמצא את כל ה-opcodes כדי לזהות מילים שלא הותאמו
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'replace':
                continue
            # כלל 3: ראשי תיבות — משתמש במילים המקוריות (עם גרשיים!)
            src_orig_slice = source_words_orig[i1:i2]
            ref_orig_slice = ref_words_orig[j1:j2]
            if is_acronym_minor_diff(src_orig_slice, ref_orig_slice):
                for k in range(i2 - i1):
                    matched[i1 + k] = True
                continue
            # כלל 1+2: שינוי קל מילה-במילה (replace 1:1 בלבד)
            if (i2 - i1) == (j2 - j1):
                for k in range(i2 - i1):
                    if is_minor_diff(source_words[i1 + k], ref_words[j1 + k]):
                        matched[i1 + k] = True

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


def build_highlighted_html(witness_text: str, base_text: str, hide_minor: bool = False) -> str:
    """מדגיש מילים בעד הנוסח שאינן מופיעות ברצף המתאים בטקסט הבסיס (וילנא)."""
    # שינוי לבקשת המשתמש: אדום מודגש ללא רקע
    style = "color:#E53E3E;font-weight:bold;"
    return _diff_highlight(witness_text, base_text, style, hide_minor=hide_minor)


def build_vilna_diff_html(base_text: str, witness_text: str, hide_minor: bool = False) -> str:
    """מדגיש מילים בטקסט וילנא שאינן מופיעות ברצף המתאים בעד הנוסח."""
    # שינוי לבקשת המשתמש: אדום מודגש ללא רקע
    style = "color:#E53E3E;font-weight:bold;"
    return _diff_highlight(base_text, witness_text, style, hide_minor=hide_minor)


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
    
    # תמיכה בראשי תיבות לפי בקשת המשתמש
    acronyms = {
        'ר"ה': 'ראש השנה',
        'מו"ק': 'מועד קטן',
        'ב"ק': 'בבא קמא',
        'ב"מ': 'בבא מציעא',
        'ב"ב': 'בבא בתרא',
        'ע"ז': 'עבודה זרה'
    }
    
    # אם השאילתה מתחילה בראשי תיבות מוכרים (גם אם אחריהם יש דף, למשל "ב"ק לז")
    for abbr, full in acronyms.items():
        if q == abbr or q.startswith(abbr + " "):
            if full in name_clean:
                return True
            
    return name_clean == q or name_clean.startswith(q) or q.startswith(name_clean)
