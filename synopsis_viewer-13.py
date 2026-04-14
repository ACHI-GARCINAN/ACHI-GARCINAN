"""
סינופסיס תלמוד בבלי - מציג עדי נוסח
הרצה: python synopsis_viewer.py [נתיב_לתיקיה_עם_קבצי_json]
"""

import sys
import json
import os
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QScrollArea, QFrame,
    QSplitter, QSizePolicy, QGraphicsDropShadowEffect, QCheckBox,
    QTextBrowser, QMessageBox, QPushButton, QLineEdit, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QFont, QColor, QCursor, QIcon, QDesktopServices


def get_base_dir() -> str:
    """
    מחזיר את תיקיית הבסיס — תקין גם בסקריפט Python וגם ב-EXE של PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_icon() -> QIcon:
    """טוען אייקון מתיקיית הבסיס (logo.ico / logo.png / icon.ico / icon.png)."""
    base = get_base_dir()
    for name in ('logo.ico', 'logo.png', 'icon.ico', 'icon.png'):
        path = os.path.join(base, name)
        if os.path.exists(path):
            return QIcon(path)
    return QIcon()


STYLE = """
QMainWindow, QWidget {
    background-color: #F7F3EC;
    font-family: 'David', 'Arial', sans-serif;
}
QListWidget#page_list {
    background-color: #2B1A0F;
    border: none;
    color: #C8A87A;
    outline: none;
    padding: 6px 0;
}
QListWidget#page_list::item {
    padding: 9px 6px;
    text-align: center;
    border-bottom: 1px solid #3A2418;
    font-size: 15px;
}
QListWidget#page_list::item:selected {
    background-color: #7A3810;
    color: #FFF5E6;
    font-weight: bold;
}
QListWidget#page_list::item:hover:!selected {
    background-color: #3A2418;
}
QListWidget#masechet_list {
    background-color: #1A2B1A;
    border: none;
    color: #A8C87A;
    outline: none;
    padding: 6px 0;
}
QListWidget#masechet_list::item {
    padding: 9px 6px;
    text-align: center;
    border-bottom: 1px solid #243424;
    font-size: 14px;
}
QListWidget#masechet_list::item:selected {
    background-color: #2E6010;
    color: #F0FFE6;
    font-weight: bold;
}
QListWidget#masechet_list::item:hover:!selected {
    background-color: #243424;
}
QScrollBar:vertical {
    background: #EDE8DF; width: 7px; border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #C0A87A; border-radius: 3px; min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QSplitter::handle { background-color: #D5C8B0; }
QCheckBox {
    color: #F0DFC0;
    font-size: 12px;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border-radius: 3px;
    border: 1px solid #C8A060;
    background: #2B1A0F;
}
QCheckBox::indicator:checked {
    background: #C8A060;
    border: 1px solid #E8C080;
}
"""

WITNESS_COLORS = [
    ("#5B3A8A", "#F0ECF8"),
    ("#1A5E8A", "#EAF3FA"),
    ("#2E7A4A", "#E8F5EE"),
    ("#8A4A1A", "#FBF0E8"),
    ("#7A1A3A", "#F8EAF0"),
    ("#2A6A6A", "#E8F5F5"),
    ("#5A6A1A", "#F2F5E8"),
    ("#6A2A6A", "#F5E8F5"),
]


def load_masechet_list(folder: str) -> list:
    pattern = re.compile(r'^(\d+)[-_\s]+\u05de\u05e1\u05db\u05ea[\s_]+(.+)\.json$')
    masechtot = []
    try:
        for fname in os.listdir(folder):
            m = pattern.match(fname)
            if m:
                num = int(m.group(1))
                name = "\u05de\u05e1\u05db\u05ea " + m.group(2).replace('_', ' ').strip()
                path = os.path.join(folder, fname)
                masechtot.append({'num': num, 'name': name, 'path': path})
    except Exception as e:
        print(f"Error reading folder: {e}")
    masechtot.sort(key=lambda x: x['num'])
    return masechtot


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
    import difflib

    # פירוק לטוקנים (מילים + רווחים)
    source_tokens = tokenize(source_text)
    ref_tokens = tokenize(reference_text)

    # רשימות המילים בלבד (ללא רווחים) עם הנרמול
    source_words = [normalize_word(t) for t in source_tokens if t.strip()]
    ref_words    = [normalize_word(t) for t in ref_tokens    if t.strip()]

    # מיפוי: אינדקס במילות-המקור → האם תואמת לייחוס
    matched = [False] * len(source_words)
    matcher = difflib.SequenceMatcher(None, source_words, ref_words, autojunk=False)
    for a, b, size in matcher.get_matching_blocks():
        for i in range(size):
            matched[a + i] = True

    # בניית ה-HTML — עוברים על כל הטוקנים (כולל רווחים) ומדגישים את שלא הותאמו
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
    style = "background-color:#FFD700;color:#3A1A00;border-radius:3px;padding:0 2px;font-weight:bold;"
    return _diff_highlight(witness_text, base_text, style)


def build_vilna_diff_html(base_text: str, witness_text: str) -> str:
    """מדגיש מילים בטקסט וילנא שאינן מופיעות ברצף המתאים בעד הנוסח."""
    style = "background-color:#FF6B35;color:#FFFFFF;border-radius:3px;padding:0 2px;font-weight:bold;"
    return _diff_highlight(base_text, witness_text, style)


# ============================================================
# מילון המרה: גימטריה → ספרה
_HEB_VALS = {
    'א': 1,  'ב': 2,  'ג': 3,  'ד': 4,  'ה': 5,
    'ו': 6,  'ז': 7,  'ח': 8,  'ט': 9,  'י': 10,
    'כ': 20, 'ך': 20, 'ל': 30, 'מ': 40, 'ם': 40,
    'נ': 50, 'ן': 50, 'ס': 60, 'ע': 70, 'פ': 80,
    'ף': 80, 'צ': 90, 'ץ': 90, 'ק': 100,'ר': 200,
    'ש': 300,'ת': 400,
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
    norm_data = _normalize_page(page_str)
    norm_query = _normalize_page(query_page)
    if norm_data == norm_query:
        return True
    val_data = _heb_to_int(norm_data)
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


# ============================================================
class SectionBlock(QFrame):
    clicked = pyqtSignal()

    def __init__(self, section: dict, main_witness: str, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.section = section
        self.main_witness = main_witness
        self.is_selected = False
        self._active_diff_witness = None
        self._plain_text = ''
        self._text_lbl = None

        self._normal_style = "QFrame#section_block{background-color:#FFFDF8;border:1px solid #E0D8C8;border-radius:8px;margin:3px 8px;}"
        self._hover_style = "QFrame#section_block{background-color:#FFF5E6;border:1px solid #C8A060;border-right:4px solid #8B4513;border-radius:8px;margin:3px 8px;}"
        self._selected_style = "QFrame#section_block{background-color:#FFF0DC;border:1px solid #8B4513;border-right:4px solid #5A1A00;border-radius:8px;margin:3px 8px;}"
        self._diff_style = "QFrame#section_block{background-color:#FFF8F0;border:1px solid #FF6B35;border-right:4px solid #CC3300;border-radius:8px;margin:3px 8px;}"

        self.setObjectName("section_block")
        self.setStyleSheet(self._normal_style)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 10, 16, 12)
        self._layout.setSpacing(6)

        tag = QLabel(section['section'])
        tag.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        tag.setStyleSheet("color:#8B4513;background-color:#F2E8D8;border-radius:4px;padding:2px 8px;")
        tag.setAlignment(Qt.AlignmentFlag.AlignRight)
        tag.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._layout.addWidget(tag, alignment=Qt.AlignmentFlag.AlignRight)

        text = section['witnesses'].get(main_witness, '') or ''
        if text == 'None': text = ''
        self._plain_text = text

        self._text_lbl = QLabel(text if text else '(\u05d0\u05d9\u05df \u05d8\u05e7\u05e1\u05d8)')
        self._text_lbl.setWordWrap(True)
        self._text_lbl.setFont(QFont("David", 16))
        self._text_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self._text_lbl.setStyleSheet("color:#1A0800;background:transparent;")
        self._layout.addWidget(self._text_lbl)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    def show_witness_diff(self, witness_name: str):
        """Toggle diff highlighting for a specific witness against Vilna text."""
        if self._active_diff_witness == witness_name:
            self._active_diff_witness = None
            self._text_lbl.setTextFormat(Qt.TextFormat.AutoText)
            self._text_lbl.setText(self._plain_text if self._plain_text else '(\u05d0\u05d9\u05df \u05d8\u05e7\u05e1\u05d8)')
            self.setStyleSheet(self._selected_style if self.is_selected else self._normal_style)
            return

        self._active_diff_witness = witness_name
        witness_text = self.section['witnesses'].get(witness_name, '') or ''
        if witness_text == 'None': witness_text = ''

        if self._plain_text and witness_text:
            html = build_vilna_diff_html(self._plain_text, witness_text)
            self._text_lbl.setTextFormat(Qt.TextFormat.RichText)
            self._text_lbl.setText(
                f'<div dir="rtl" style="font-family:David,serif;font-size:16pt;color:#1A0800;">{html}</div>'
            )
        self.setStyleSheet(self._diff_style)

    def clear_diff(self):
        self._active_diff_witness = None
        self._text_lbl.setTextFormat(Qt.TextFormat.AutoText)
        self._text_lbl.setText(self._plain_text if self._plain_text else '(\u05d0\u05d9\u05df \u05d8\u05e7\u05e1\u05d8)')
        self.setStyleSheet(self._selected_style if self.is_selected else self._normal_style)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        if self._active_diff_witness:
            self.setStyleSheet(self._diff_style)
        else:
            self.setStyleSheet(self._selected_style if selected else self._normal_style)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def enterEvent(self, event):
        if not self.is_selected and not self._active_diff_witness:
            self.setStyleSheet(self._hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_selected and not self._active_diff_witness:
            self.setStyleSheet(self._normal_style)
        elif self._active_diff_witness:
            self.setStyleSheet(self._diff_style)
        super().leaveEvent(event)


# ============================================================
class WitnessCard(QFrame):
    clicked = pyqtSignal(str)  # emits witness name

    def __init__(self, name: str, text, color_pair: tuple,
                 base_text: str = '', highlight: bool = False,
                 clickable: bool = False, parent=None):
        super().__init__(parent)
        accent, bg = color_pair
        self.witness_name = name
        self.clickable = clickable
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        if clickable and text:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        if text:
            self.setStyleSheet(f"QFrame{{background-color:{bg};border:1px solid {accent}35;border-top:3px solid {accent};border-radius:10px;margin:4px 8px;}}")
        else:
            self.setStyleSheet("QFrame{background-color:#F0EDE6;border:1px dashed #C5B89A;border-radius:10px;margin:4px 8px;}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(6)

        name_lbl = QLabel(name)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        name_lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        if text:
            name_lbl.setStyleSheet(f"color:{accent};background:transparent;border:1px solid {accent};border-radius:5px;padding:3px 8px;")
        else:
            name_lbl.setStyleSheet("color:#A09080;background:transparent;border:1px solid #C5B89A;border-radius:5px;padding:3px 8px;")
        layout.addWidget(name_lbl)

        if text:
            if highlight and base_text:
                html_content = build_highlighted_html(text, base_text)
                txt_widget = QTextBrowser()
                txt_widget.setOpenLinks(False)
                txt_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                txt_widget.setHtml(
                    f'<div dir="rtl" style="font-family:David,serif;font-size:15pt;'
                    f'color:#1A0A00;text-align:right;">{html_content}</div>'
                )
                txt_widget.setStyleSheet("QTextBrowser{background:transparent;border:none;color:#1A0A00;}")
                txt_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
                txt_widget.document().adjustSize()
                h = int(txt_widget.document().size().height()) + 16
                txt_widget.setFixedHeight(max(50, h))
                layout.addWidget(txt_widget)
            else:
                txt_lbl = QLabel(text)
                txt_lbl.setWordWrap(True)
                txt_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
                txt_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                txt_lbl.setFont(QFont("David", 15))
                txt_lbl.setStyleSheet("color:#1A0A00;background:transparent;")
                layout.addWidget(txt_lbl)
        else:
            miss = QLabel("\u05d0\u05d9\u05df \u05e2\u05d3 \u05e0\u05d5\u05e1\u05d7 \u05dc\u05e7\u05d8\u05e2 \u05d6\u05d4")
            miss.setAlignment(Qt.AlignmentFlag.AlignRight)
            miss.setStyleSheet("color:#B0A090;font-style:italic;font-size:12px;background:transparent;")
            layout.addWidget(miss)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 18))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.clickable:
            self.clicked.emit(self.witness_name)
        super().mousePressEvent(event)


# ============================================================
class WitnessPanel(QWidget):
    witness_clicked = pyqtSignal(str)  # emits witness name when card clicked in highlight mode

    def __init__(self, witnesses: list, parent=None):
        super().__init__(parent)
        self.witnesses = witnesses
        self.highlight_diffs = False
        self.hide_empty_witnesses = True
        self._current_section = None
        self._current_page = ''
        self._base_text = ''

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet("background-color:#EDE8DF;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # כותרת + צ'קבוקס
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color:#3A2010;border-bottom:2px solid #C8A060;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 10, 16, 8)
        header_layout.setSpacing(5)

        self.header = QLabel("\u05d1\u05d7\u05e8 \u05e7\u05d8\u05e2 \u05dc\u05e2\u05d3\u05d9 \u05e0\u05d5\u05e1\u05d7")
        self.header.setFont(QFont("David", 14, QFont.Weight.Bold))
        self.header.setStyleSheet("color:#F0DFC0;background:transparent;border:none;")
        self.header.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.header)

        self.highlight_cb = QCheckBox("\u05d4\u05d3\u05d2\u05e9 \u05e9\u05d9\u05e0\u05d5\u05d9\u05d9\u05dd \u05de\u05d5\u05d9\u05dc\u05e0\u05d0")
        self.highlight_cb.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.highlight_cb.setFont(QFont("Arial", 10))
        self.highlight_cb.setChecked(False)
        self.highlight_cb.stateChanged.connect(self._on_highlight_changed)
        header_layout.addWidget(self.highlight_cb, alignment=Qt.AlignmentFlag.AlignRight)

        self.hide_empty_cb = QCheckBox("\u05d4\u05e1\u05ea\u05e8 \u05e2\u05d3\u05d9 \u05e0\u05d5\u05e1\u05d7 \u05e8\u05d9\u05e7\u05d9\u05dd")
        self.hide_empty_cb.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.hide_empty_cb.setFont(QFont("Arial", 10))
        self.hide_empty_cb.setChecked(True)
        self.hide_empty_cb.stateChanged.connect(self._on_hide_empty_changed)
        header_layout.addWidget(self.hide_empty_cb, alignment=Qt.AlignmentFlag.AlignRight)

        self.hint_label = QLabel("\u05dc\u05d7\u05e5 \u05e2\u05dc \u05e7\u05d8\u05e2 \u05db\u05d3\u05d9 \u05dc\u05e8\u05d0\u05d5\u05ea \u05d0\u05ea \u05d4\u05e9\u05d9\u05e0\u05d5\u05d9\u05d9\u05dd \u05d1\u05d8\u05e7\u05e1\u05d8 \u05d4\u05de\u05e8\u05db\u05d6\u05d9")
        self.hint_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.hint_label.setFont(QFont("Arial", 9))
        self.hint_label.setStyleSheet("color:#E8C080;background:transparent;border:none;font-style:italic;")
        self.hint_label.setVisible(False)
        header_layout.addWidget(self.hint_label, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(header_widget)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea{border:none;background:#EDE8DF;}")

        self.container = QWidget()
        self.container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.container.setStyleSheet("background-color:#EDE8DF;")
        self.inner_layout = QVBoxLayout(self.container)
        self.inner_layout.setContentsMargins(4, 10, 4, 20)
        self.inner_layout.setSpacing(4)

        self._show_placeholder()

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

    def update_witnesses(self, witnesses: list):
        self.witnesses = witnesses

    def _on_highlight_changed(self, state):
        self.highlight_diffs = (state == Qt.CheckState.Checked.value)
        self.hint_label.setVisible(self.highlight_diffs)
        if self._current_section is not None:
            self.show_section(self._current_section, self._current_page, self._base_text)

    def _on_hide_empty_changed(self, state):
        self.hide_empty_witnesses = (state == Qt.CheckState.Checked.value)
        if self._current_section is not None:
            self.show_section(self._current_section, self._current_page, self._base_text)

    def _show_placeholder(self):
        ph = QLabel("\u2190  \u05dc\u05d7\u05e5 \u05e2\u05dc \u05e7\u05d8\u05e2 \u05d1\u05d8\u05e7\u05e1\u05d8\n\u05db\u05d3\u05d9 \u05dc\u05e8\u05d0\u05d5\u05ea \u05d0\u05ea \u05e2\u05d3\u05d9 \u05d4\u05e0\u05d5\u05e1\u05d7")
        ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph.setStyleSheet("color:#B0A080;font-size:14px;padding:50px 20px;background:transparent;")
        self.inner_layout.addStretch()
        self.inner_layout.addWidget(ph)
        self.inner_layout.addStretch()

    def _clear(self):
        while self.inner_layout.count():
            item = self.inner_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def show_section(self, section: dict, page: str, base_text: str = ''):
        self._current_section = section
        self._current_page = page
        self._base_text = base_text
        self._clear()

        self.header.setText(f"\u05d3\u05e3 {page}  \u00b7  {section['section']}")

        witness_data = section.get('witnesses', {})

        for i, witness in enumerate(self.witnesses):
            text = witness_data.get(witness)
            if text == 'None' or text == '':
                text = None
            if text is None and self.hide_empty_witnesses:
                continue
            color = WITNESS_COLORS[i % len(WITNESS_COLORS)]
            card = WitnessCard(
                witness, text, color,
                base_text=base_text,
                highlight=self.highlight_diffs,
                clickable=self.highlight_diffs
            )
            if self.highlight_diffs and text:
                card.clicked.connect(self.witness_clicked.emit)
            self.inner_layout.addWidget(card)

        self.inner_layout.addStretch()
        self.scroll.verticalScrollBar().setValue(0)

    def reset(self):
        self._current_section = None
        self._current_page = ''
        self._base_text = ''
        self._clear()
        self.header.setText("\u05d1\u05d7\u05e8 \u05e7\u05d8\u05e2 \u05dc\u05e2\u05d3\u05d9 \u05e0\u05d5\u05e1\u05d7")
        self._show_placeholder()


# ============================================================
class _CopyrightPopup(QWidget):
    """
    פופ-אפ overlay: מכסה את כל חלון-האב בשכבה שקופה למחצה,
    במרכזה מלבן עם קצוות מעוגלים. לחיצה מחוץ למלבן → סגירה.
    """
    MAIL = "talmud1239@gmail.com"

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setGeometry(parent.rect())          # כיסוי מלא של החלון
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # --- כרטיס פנימי ---
        self._card = QFrame(self)
        self._card.setObjectName("popup_frame")
        self._card.setStyleSheet("""
            QFrame#popup_frame {
                background-color: #FFFDF8;
                border: 2px solid #C8A060;
                border-radius: 16px;
            }
        """)
        self._card.setFixedWidth(480)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(35)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self._card.setGraphicsEffect(shadow)

        inner = QVBoxLayout(self._card)
        inner.setContentsMargins(30, 26, 30, 26)
        inner.setSpacing(14)

        # כותרת
        title = QLabel("הערת שימוש")
        title.setFont(QFont("David", 15, QFont.Weight.Bold))
        title.setStyleSheet("color:#5A1A00;background:transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(title)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:#D5C8A0;max-height:1px;border:none;")
        inner.addWidget(sep)

        # גוף
        body = QLabel(
            "שים לב כי כל החומר כאן לוקט מתוכן השייך משפטית לאתר\n"
            "\u201cפרידברג \u2013 הכי גרסינן\u201d,\n\n"
            "והשימוש בו מותר אך ורק לצורך שימוש פרטי ולא לצורך מסחרי!"
        )
        body.setFont(QFont("David", 13))
        body.setStyleSheet("color:#2A1000;background:transparent;")
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)
        inner.addWidget(body)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background:#D5C8A0;max-height:1px;border:none;")
        inner.addWidget(sep2)

        # שורת מייל
        contact_row = QHBoxLayout()
        contact_row.setSpacing(6)

        contact_lbl = QLabel("תגובות והערות ניתן לכתוב במייל")
        contact_lbl.setFont(QFont("David", 12))
        contact_lbl.setStyleSheet("color:#5A3A10;background:transparent;")
        contact_row.addWidget(contact_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        # כפתור-קישור למייל (פותח את תוכנת המייל של המערכת)
        mail_btn = QPushButton(self.MAIL)
        mail_btn.setFont(QFont("Arial", 11))
        mail_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        mail_btn.setStyleSheet("""
            QPushButton {
                color:#1A5E8A; background:transparent;
                border:none; padding:0; text-decoration:underline;
            }
            QPushButton:hover { color:#0A3E6A; }
        """)
        mail_btn.clicked.connect(self._open_mail)
        contact_row.addWidget(mail_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        # כפתור העתקה
        copy_btn = QPushButton("📋")
        copy_btn.setToolTip("העתק כתובת מייל")
        copy_btn.setFixedSize(26, 26)
        copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        copy_btn.setFont(QFont("Arial", 13))
        copy_btn.setStyleSheet("""
            QPushButton {
                background:transparent; border:none; padding:0;
            }
            QPushButton:hover { background:rgba(0,0,0,0.07); border-radius:5px; }
        """)
        copy_btn.clicked.connect(self._copy_mail)
        contact_row.addWidget(copy_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        contact_row.addStretch()
        inner.addLayout(contact_row)

        # מרכוז הכרטיס
        card_layout = QVBoxLayout(self)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self._card, 0, Qt.AlignmentFlag.AlignCenter)

        self.raise_()
        self.show()

    # ------------------------------------------------------------------ #
    def _open_mail(self):
        import subprocess, sys as _sys
        if _sys.platform == "win32":
            import os
            os.startfile(f"mailto:{self.MAIL}")
        else:
            QDesktopServices.openUrl(QUrl(f"mailto:{self.MAIL}"))

    def _copy_mail(self):
        QApplication.clipboard().setText(self.MAIL)
        # אישור חזותי קצר
        sender = self.sender()
        sender.setText("✓")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1200, lambda: sender.setText("📋"))

    def mousePressEvent(self, event):
        """לחיצה מחוץ לכרטיס → סגור."""
        if not self._card.geometry().contains(event.position().toPoint()):
            self.close()
        else:
            super().mousePressEvent(event)

    def exec(self):
        """ממשק תואם ל-QDialog.exec() – נכנס ללולאת אירועים עד לסגירה."""
        loop = __import__('PyQt6.QtCore', fromlist=['QEventLoop']).QEventLoop()
        self.destroyed.connect(loop.quit)
        loop.exec()

    def close(self):
        super().close()
        self.deleteLater()


# ============================================================
class MainWindow(QMainWindow):
    def __init__(self, masechtot: list):
        super().__init__()
        self.masechtot = masechtot
        self.current_data = None
        self.current_masechet_name = ""
        self.witnesses = []
        self.pages = []
        self.main_witness = ''
        self.current_page_idx = 0
        self.selected_block = None
        self.section_blocks = []

        self.setWindowTitle("\u05e1\u05d9\u05e0\u05d5\u05e4\u05e1\u05d9\u05e1 \u05ea\u05dc\u05de\u05d5\u05d3 \u05d1\u05d1\u05dc\u05d9")
        self.setMinimumSize(1100, 650)
        self.resize(1500, 860)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(STYLE)
        self.setWindowIcon(get_icon())

        self._build_ui()

        if self.masechtot:
            self.masechet_list.setCurrentRow(0)


    def _show_copyright_notice(self):
        popup = _CopyrightPopup(self.centralWidget())
        popup.exec()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(2)
        root.addWidget(self.splitter)

        self.witness_panel = WitnessPanel([])
        self.witness_panel.setMinimumWidth(280)
        self.witness_panel.witness_clicked.connect(self._on_witness_card_clicked)

        main_area = QWidget()
        main_area.setStyleSheet("background-color:#F7F3EC;")
        ma_layout = QVBoxLayout(main_area)
        ma_layout.setContentsMargins(0, 0, 0, 0)
        ma_layout.setSpacing(0)

        header = QWidget()
        header.setStyleSheet("background-color:#2B1A0F;")
        h_outer = QHBoxLayout(header)
        h_outer.setContentsMargins(20, 14, 20, 10)
        h_outer.setSpacing(10)

        # אזור כותרות (ימין)
        titles_widget = QWidget()
        titles_widget.setStyleSheet("background:transparent;")
        h_layout = QVBoxLayout(titles_widget)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(2)

        self.page_title = QLabel("")
        self.page_title.setFont(QFont("David", 20, QFont.Weight.Bold))
        self.page_title.setStyleSheet("color:#FFF5E6;background:transparent;")
        self.page_title.setAlignment(Qt.AlignmentFlag.AlignRight)
        h_layout.addWidget(self.page_title)

        self.page_sub = QLabel("")
        self.page_sub.setFont(QFont("Arial", 10))
        self.page_sub.setStyleSheet("color:#C8A87A;background:transparent;")
        self.page_sub.setAlignment(Qt.AlignmentFlag.AlignRight)
        h_layout.addWidget(self.page_sub)

        h_outer.addWidget(titles_widget, 1)

        # כפתור אזהרת זכויות יוצרים (שמאל) – עיגול עם סימן קריאה הפוך
        warn_btn = QPushButton("¡")
        warn_btn.setToolTip("הערת שימוש")
        warn_btn.setFixedSize(30, 30)
        warn_btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        warn_btn.setStyleSheet("""
            QPushButton {
                color: #C8A060;
                background: transparent;
                border: 2px solid #A08040;
                border-radius: 15px;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                color: #FFD070;
                border-color: #E0B050;
                background: rgba(200,160,60,0.15);
            }
        """)
        warn_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        warn_btn.clicked.connect(self._show_copyright_notice)
        h_outer.addWidget(warn_btn, 0, Qt.AlignmentFlag.AlignBottom)

        # תיבת איתור מהיר
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText('חפש מסכת ודף... (למשל: ברכות לג, שבת ל"ג)')
        self.search_box.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.search_box.setFont(QFont('David', 12))
        self.search_box.setFixedWidth(260)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #3A2418;
                color: #FFF5E6;
                border: 1px solid #6A4020;
                border-radius: 6px;
                padding: 5px 10px;
                selection-background-color: #7A3810;
            }
            QLineEdit:focus {
                border: 1px solid #C8A060;
                background-color: #4A2E1A;
            }
            QLineEdit::placeholder {
                color: #806040;
            }
        """)
        self.search_box.returnPressed.connect(self._quick_nav)
        h_outer.addWidget(self.search_box, 0, Qt.AlignmentFlag.AlignVCenter)

        ma_layout.addWidget(header)

        self.text_scroll = QScrollArea()
        self.text_scroll.setWidgetResizable(True)
        self.text_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_scroll.setStyleSheet("QScrollArea{border:none;background:#F7F3EC;}")

        self.text_container = QWidget()
        self.text_container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.text_container.setStyleSheet("background-color:#F7F3EC;")
        self.text_layout = QVBoxLayout(self.text_container)
        self.text_layout.setContentsMargins(12, 14, 12, 30)
        self.text_layout.setSpacing(8)
        self.text_layout.addStretch()

        self.text_scroll.setWidget(self.text_container)
        ma_layout.addWidget(self.text_scroll, 1)

        page_panel = QWidget()
        page_panel.setStyleSheet("background-color:#2B1A0F;")
        pp_layout = QVBoxLayout(page_panel)
        pp_layout.setContentsMargins(0, 0, 0, 0)
        pp_layout.setSpacing(0)

        pg_hdr = QLabel("\u05d3\u05e4\u05d9\u05dd")
        pg_hdr.setFont(QFont("Arial", 10))
        pg_hdr.setStyleSheet("color:#C8A060;padding:10px 6px 8px 6px;letter-spacing:2px;border-bottom:1px solid #3A2418;")
        pg_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pp_layout.addWidget(pg_hdr)

        self.page_list = QListWidget()
        self.page_list.setObjectName("page_list")
        self.page_list.setFont(QFont("David", 14))
        self.page_list.setFixedWidth(85)
        self.page_list.currentRowChanged.connect(self._load_page)
        pp_layout.addWidget(self.page_list, 1)

        masechet_panel = QWidget()
        masechet_panel.setStyleSheet("background-color:#1A2B1A;")
        mp_layout = QVBoxLayout(masechet_panel)
        mp_layout.setContentsMargins(0, 0, 0, 0)
        mp_layout.setSpacing(0)

        ms_hdr = QLabel("\u05de\u05e1\u05db\u05ea\u05d5\u05ea")
        ms_hdr.setFont(QFont("Arial", 10))
        ms_hdr.setStyleSheet("color:#A8C060;padding:10px 6px 8px 6px;letter-spacing:2px;border-bottom:1px solid #243424;")
        ms_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mp_layout.addWidget(ms_hdr)

        self.masechet_list = QListWidget()
        self.masechet_list.setObjectName("masechet_list")
        self.masechet_list.setFont(QFont("David", 13))
        self.masechet_list.setFixedWidth(130)

        for ms in self.masechtot:
            item = QListWidgetItem(ms['name'])
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.masechet_list.addItem(item)

        self.masechet_list.currentRowChanged.connect(self._load_masechet)
        mp_layout.addWidget(self.masechet_list, 1)

        self.splitter.addWidget(masechet_panel)
        self.splitter.addWidget(page_panel)
        self.splitter.addWidget(main_area)
        self.splitter.addWidget(self.witness_panel)
        self.splitter.setSizes([130, 85, 780, 420])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 0)
        self.splitter.setStretchFactor(2, 1)
        self.splitter.setStretchFactor(3, 0)

    def _quick_nav(self):
        raw = self.search_box.text().strip()
        if not raw:
            return

        # ניתוח הקלט: מחלצים שם מסכת ומספר דף
        # תבנית: <מסכת> [דף] <מספר>
        m = re.match(
            r'^([\u05d0-\u05ea]+(?:\s[\u05d0-\u05ea]+)*)'
            r'(?:\s+\u05d3\u05e3)?'
            r'\s+([\u05d0-\u05ea"\u05f4\u05f3\u2019\']+|\d+)$',
            raw
        )
        if not m:
            self.search_box.setStyleSheet(
                self.search_box.styleSheet() +
                'QLineEdit { border: 1px solid #CC3300; }'
            )
            return

        ms_query = m.group(1).strip()
        pg_query = m.group(2).strip()

        # מצא את המסכת
        ms_idx = None
        for i, ms in enumerate(self.masechtot):
            if _masechet_matches(ms['name'], ms_query):
                ms_idx = i
                break

        if ms_idx is None:
            self.search_box.setStyleSheet(
                self.search_box.styleSheet() +
                'QLineEdit { border: 1px solid #CC3300; }'
            )
            return

        # טען את המסכת אם צריך
        if self.masechet_list.currentRow() != ms_idx:
            self.masechet_list.setCurrentRow(ms_idx)

        # מצא את הדף
        pg_idx = None
        for i, pg in enumerate(self.pages):
            if _page_matches(pg['page'], pg_query):
                pg_idx = i
                break

        if pg_idx is None:
            self.search_box.setStyleSheet(
                self.search_box.styleSheet() +
                'QLineEdit { border: 1px solid #CC3300; }'
            )
            return

        self.page_list.setCurrentRow(pg_idx)
        self.search_box.clear()
        # החזר סגנון רגיל
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #3A2418;
                color: #FFF5E6;
                border: 1px solid #6A4020;
                border-radius: 6px;
                padding: 5px 10px;
                selection-background-color: #7A3810;
            }
            QLineEdit:focus {
                border: 1px solid #C8A060;
                background-color: #4A2E1A;
            }
        """)

    def _load_masechet(self, idx: int):
        if idx < 0 or idx >= len(self.masechtot):
            return

        ms = self.masechtot[idx]
        try:
            with open(ms['path'], 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.page_title.setText(f"Error: {e}")
            return

        self.current_data = data
        self.current_masechet_name = ms['name']
        self.witnesses = data.get('witnesses', [])
        self.pages = data.get('pages', [])
        self.main_witness = self.witnesses[0] if self.witnesses else ''
        self.selected_block = None
        self.section_blocks = []

        self.witness_panel.update_witnesses(self.witnesses)
        self.witness_panel.reset()

        self.page_sub.setText(f"\u05d8\u05e7\u05e1\u05d8: {self.main_witness}" if self.main_witness else "")

        self.page_list.blockSignals(True)
        self.page_list.clear()
        for pg in self.pages:
            item = QListWidgetItem(pg['page'])
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.page_list.addItem(item)
        self.page_list.blockSignals(False)

        self._clear_text()
        self.page_title.setText(self.current_masechet_name)

        if self.pages:
            self.page_list.setCurrentRow(0)

    def _load_page(self, idx: int):
        if idx < 0 or idx >= len(self.pages):
            return

        self.current_page_idx = idx
        self.selected_block = None
        self.section_blocks = []
        page = self.pages[idx]

        self.page_title.setText(f"{self.current_masechet_name} \u00b7 \u05d3\u05e3 {page['page']}")

        self._clear_text()

        for section in page['sections']:
            block = SectionBlock(section, self.main_witness)
            block.clicked.connect(
                lambda checked=False, s=section, b=block, p=page['page']:
                    self._select_section(s, b, p)
            )
            self.text_layout.insertWidget(self.text_layout.count() - 1, block)
            self.section_blocks.append(block)

        self.text_scroll.verticalScrollBar().setValue(0)
        self.witness_panel.reset()

    def _clear_text(self):
        while self.text_layout.count() > 1:
            item = self.text_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _select_section(self, section: dict, block, page: str):
        if self.selected_block and self.selected_block is not block:
            self.selected_block.set_selected(False)
            self.selected_block.clear_diff()
        block.set_selected(True)
        self.selected_block = block

        base_text = section['witnesses'].get(self.main_witness, '') or ''
        if base_text == 'None':
            base_text = ''

        self.witness_panel.show_section(section, page, base_text)

    def _on_witness_card_clicked(self, witness_name: str):
        """When a witness card is clicked in highlight mode, show diffs on the selected central block."""
        if not self.selected_block:
            return
        self.selected_block.show_witness_diff(witness_name)


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setWindowIcon(get_icon())

    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = get_base_dir()

    masechtot = load_masechet_list(folder)

    if not masechtot:
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(None, "\u05d1\u05d7\u05e8 \u05ea\u05d9\u05e7\u05d9\u05d4", "")
        if not folder:
            sys.exit(0)
        masechtot = load_masechet_list(folder)

    if not masechtot:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "\u05e9\u05d2\u05d9\u05d0\u05d4", "\u05dc\u05d0 \u05e0\u05de\u05e6\u05d0\u05d5 \u05e7\u05d1\u05e6\u05d9 JSON.")
        sys.exit(1)

    window = MainWindow(masechtot)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
