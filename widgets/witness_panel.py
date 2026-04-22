from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QCheckBox,
    QFrame, QSizePolicy, QTextBrowser, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from styles import WITNESS_COLORS, get_theme_styles, get_theme_config
from widgets.witness_card import WitnessCard
from settings_manager import load_settings, save_settings


def normalize_word(w: str) -> str:
    import re
    if not w: return ""
    w = re.sub(r'[\u05B0-\u05C7]', '', w)
    w = re.sub(r'[\u05f3\u05f4",.\-:;!?()\[\]]', '', w)
    return w.strip()


class WitnessPanel(QWidget):
    witness_clicked = pyqtSignal(str)

    def __init__(self, witnesses: list, font_family: str = 'David', font_size: int = 15, theme: str = 'classic', parent=None):
        super().__init__(parent)
        self.witnesses = witnesses
        # Load saved checkbox states
        _saved = load_settings()
        self.highlight_diffs = _saved.get('highlight_diffs', False)
        self.hide_empty_witnesses = _saved.get('hide_empty_witnesses', True)
        self.hide_minor_diffs = _saved.get('hide_minor_diffs', False)
        self._font_family = font_family
        self._font_size = font_size
        self._theme = theme

        # State for re-rendering
        self._current_section = None
        self._current_page = ''
        self._base_text = ''
        self._word_mode = False
        self._words_data = None
        self._word_idx = -1
        self._main_witness = ''

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.header_widget = QWidget()
        self.header_layout = QVBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(16, 10, 16, 8)
        self.header_layout.setSpacing(5)

        self.header_label = QLabel("בחר קטע לעדי נוסח")
        self.header_label.setFont(QFont("David", 14, QFont.Weight.Bold))
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.header_layout.addWidget(self.header_label)

        self.highlight_cb = QCheckBox("הדגש שינויים מוילנא")
        self.highlight_cb.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.highlight_cb.setFont(QFont("Arial", 10))
        self.highlight_cb.setChecked(self.highlight_diffs)
        self.highlight_cb.stateChanged.connect(self._on_highlight_changed)

        self.hide_empty_cb = QCheckBox("הסתר עדי נוסח ריקים")
        self.hide_empty_cb.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.hide_empty_cb.setFont(QFont("Arial", 10))
        self.hide_empty_cb.setChecked(self.hide_empty_witnesses)
        self.hide_empty_cb.stateChanged.connect(self._on_hide_empty_changed)

        self.hide_minor_cb = QCheckBox("הסתר שינויים קלים")
        self.hide_minor_cb.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.hide_minor_cb.setFont(QFont("Arial", 10))
        self.hide_minor_cb.setChecked(self.hide_minor_diffs)
        self.hide_minor_cb.setEnabled(self.highlight_diffs)
        self.hide_minor_cb.stateChanged.connect(self._on_hide_minor_changed)

        cb_row = QWidget()
        cb_row.setStyleSheet("background:transparent;border:none;")
        cb_layout = QHBoxLayout(cb_row)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        cb_layout.setSpacing(10)
        cb_layout.addWidget(self.hide_minor_cb)
        cb_layout.addWidget(self.hide_empty_cb)
        cb_layout.addWidget(self.highlight_cb)
        self.header_layout.addWidget(cb_row, alignment=Qt.AlignmentFlag.AlignRight)

        self.hint_label = QLabel("לחץ על קטע כדי לראות את השינויים בטקסט המרכזי")
        self.hint_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.hint_label.setFont(QFont("Arial", 9))
        self.hint_label.setVisible(False)
        self.header_layout.addWidget(self.hint_label, alignment=Qt.AlignmentFlag.AlignRight)

        self.main_layout.addWidget(self.header_widget)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.inner_layout = QVBoxLayout(self.container)
        self.inner_layout.setContentsMargins(4, 10, 4, 20)
        self.inner_layout.setSpacing(4)

        self.scroll.setWidget(self.container)
        self.main_layout.addWidget(self.scroll, 1)
        
        self._update_ui_colors()
        self._show_placeholder()

    def _update_ui_colors(self):
        cfg = get_theme_config(self._theme)
        self.header_widget.setStyleSheet(f"background-color:{cfg['panel_header_bg']};border-bottom:2px solid {cfg['panel_header_border']};")
        self.header_label.setStyleSheet(f"color:{cfg['panel_header_text']};background:transparent;border:none;")
        self.hint_label.setStyleSheet(f"color:{cfg['panel_hint_text']};background:transparent;border:none;font-style:italic;")
        self.scroll.setStyleSheet(f"QScrollArea{{border:none;background:{cfg['main_bg']};}}")
        self.container.setStyleSheet(f"background-color:{cfg['main_bg']};")
        
        cb_style = f"color: {cfg['panel_header_text'] if self._theme == 'colorful' else '#4A5568'};"
        self.highlight_cb.setStyleSheet(cb_style)
        self.hide_empty_cb.setStyleSheet(cb_style)
        self.hide_minor_cb.setStyleSheet(cb_style)

    def update_witnesses(self, witnesses: list):
        self.witnesses = witnesses

    def update_font(self, font_family: str, font_size: int, theme: str = None):
        self._font_family = font_family
        self._font_size = font_size
        if theme:
            self._theme = theme
            self._update_ui_colors()
        
        if self._word_mode and self._current_section is not None:
            self.show_word(self._current_section, self._current_page, self._main_witness,
                           self._words_data, self._word_idx)
        elif not self._word_mode and self._current_section is not None:
            self.show_section(self._current_section, self._current_page, self._base_text)

    def _on_highlight_changed(self, state):
        if isinstance(state, int):
            self.highlight_diffs = (state == 2)
        else:
            self.highlight_diffs = bool(state)
        save_settings({'highlight_diffs': self.highlight_diffs})
        
        self.hide_minor_cb.setEnabled(self.highlight_diffs)
            
        self.hint_label.setVisible(self.highlight_diffs and not self._word_mode)
        if self._word_mode and self._words_data is not None:
            self.show_word(self._current_section, self._current_page, self._main_witness,
                           words_data=self._words_data, word_idx=self._word_idx)
        elif self._current_section is not None:
            self.show_section(self._current_section, self._current_page, self._base_text)

    def _on_hide_empty_changed(self, state):
        if isinstance(state, int):
            self.hide_empty_witnesses = (state == 2)
        else:
            self.hide_empty_witnesses = bool(state)
        save_settings({'hide_empty_witnesses': self.hide_empty_witnesses})
            
        if self._word_mode and self._words_data is not None:
            self.show_word(self._current_section, self._current_page, self._main_witness,
                           words_data=self._words_data, word_idx=self._word_idx)
        elif self._current_section is not None:
            self.show_section(self._current_section, self._current_page, self._base_text)

    def _on_hide_minor_changed(self, state):
        if isinstance(state, int):
            self.hide_minor_diffs = (state == 2)
        else:
            self.hide_minor_diffs = bool(state)
        save_settings({'hide_minor_diffs': self.hide_minor_diffs})
            
        if self._word_mode and self._words_data is not None:
            self.show_word(self._current_section, self._current_page, self._main_witness,
                           words_data=self._words_data, word_idx=self._word_idx)
        elif self._current_section is not None:
            self.show_section(self._current_section, self._current_page, self._base_text)

    def _show_placeholder(self):
        self._clear()
        cfg = get_theme_config(self._theme)
        ph = QLabel("←  לחץ על קטע בטקסט\nכדי לראות את עדי הנוסח")
        ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph.setStyleSheet(f"color:{cfg['panel_hint_text']};font-size:14px;padding:50px 20px;background:transparent;")
        self.inner_layout.addStretch()
        self.inner_layout.addWidget(ph)
        self.inner_layout.addStretch()

    def _clear(self):
        while self.inner_layout.count():
            item = self.inner_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            else:
                self.inner_layout.removeItem(item)

    def reset(self):
        self._current_section = None
        self._show_placeholder()

    def show_section(self, section: dict, page: str, base_text: str = ''):
        self._current_section = section
        self._current_page = page
        self._base_text = base_text
        self._word_mode = False
        self._words_data = None
        self._word_idx = -1
        self._clear()

        self.header_label.setText(f"דף {page}  ·  {section['section']}")

        witness_data = section.get('witnesses', {})

        _, theme_colors = get_theme_styles(self._theme)
        for i, witness in enumerate(self.witnesses):
            if i == 0:
                continue  # העד הראשון (וילנא) הוא הטקסט המרכזי - אין ענין להציגו
            text = witness_data.get(witness)
            if text == 'None' or text == '':
                text = None
            if text is None and self.hide_empty_witnesses:
                continue
            color = theme_colors[i % len(theme_colors)]
            card = WitnessCard(
                witness, text, color,
                base_text=base_text,
                highlight=self.highlight_diffs,
                clickable=self.highlight_diffs,
                font_family=self._font_family,
                font_size=self._font_size,
                hide_minor=self.hide_minor_diffs
            )
            if self.highlight_diffs and text:
                card.clicked.connect(self.witness_clicked.emit)
            self.inner_layout.addWidget(card)

        self.inner_layout.addStretch()
        self.scroll.verticalScrollBar().setValue(0)

    def show_word(self, word_entry: dict, page: str, main_witness: str,
                  words_data: list = None, word_idx: int = -1):
        self._current_section = word_entry
        self._current_page = page
        self._base_text = ''
        self._word_mode = True
        self._words_data = words_data
        self._word_idx = word_idx
        self._main_witness = main_witness
        self._clear()

        section_label = word_entry.get('section', '')
        main_text = word_entry['witnesses'].get(main_witness) or ''
        if main_text == 'None':
            main_text = ''

        self.header_label.setText(f"דף {page}  ·  {section_label}  ·  מילה: {main_text or '—'}")

        CONTEXT = 12
        vilna_word = (word_entry['witnesses'].get(main_witness) or '').strip()
        if vilna_word == 'None':
            vilna_word = ''

        for i, witness in enumerate(self.witnesses):
            if i == 0:
                continue  # העד הראשון (וילנא) הוא הטקסט המרכזי - אין ענין להציגו
            if words_data is not None and word_idx >= 0:
                before_parts = []
                for j in range(max(0, word_idx - CONTEXT), word_idx):
                    t = words_data[j]['witnesses'].get(witness) or ''
                    if t == 'None': t = ''
                    before_parts.append(t if t else '—')

                sel_text = words_data[word_idx]['witnesses'].get(witness) or ''
                if sel_text == 'None': sel_text = ''
                selected_word = sel_text if sel_text else '—'

                after_parts = []
                for j in range(word_idx + 1, min(len(words_data), word_idx + CONTEXT + 1)):
                    t = words_data[j]['witnesses'].get(witness) or ''
                    if t == 'None': t = ''
                    after_parts.append(t if t else '—')

                has_any_in_context = bool(sel_text) or any(
                    (words_data[j]['witnesses'].get(witness) or '').strip() not in ('', 'None')
                    for j in range(max(0, word_idx - CONTEXT), min(len(words_data), word_idx + CONTEXT + 1))
                )
                
                if not has_any_in_context and self.hide_empty_witnesses:
                    continue

                is_vilna = (witness == main_witness)
                if self.highlight_diffs and not is_vilna:
                    from utils import is_minor_diff
                    norm_sel = normalize_word(sel_text)
                    norm_vil = normalize_word(vilna_word)
                    # שינוי: גם כשיש מילה בוילנא אבל אין בעד הנוסח (קו) - זה שינוי
                    missing_in_witness = bool(vilna_word) and not bool(sel_text)
                    word_differs = missing_in_witness or (bool(sel_text) and (norm_sel != norm_vil))
                    if word_differs and not missing_in_witness and self.hide_minor_diffs:
                        if is_minor_diff(sel_text, vilna_word):
                            word_differs = False
                    if word_differs:
                        highlight_style = "background-color: #FFD700; color: #000000; font-weight: bold; border-radius: 2px;"
                        selected_word = f'<span style="{highlight_style}">{selected_word}</span>'

                before_str = " ".join(before_parts)
                after_str = " ".join(after_parts)
                full_html = f'<div dir="rtl" style="font-family:{self._font_family},serif; font-size:{self._font_size}pt; line-height:1.4; text-align:left;">'
                full_html += f'<span style="color:#888888;">{before_str}</span> '
                full_html += f'<b>{selected_word}</b> '
                full_html += f'<span style="color:#888888;">{after_str}</span>'
                full_html += '</div>'

                _, theme_colors = get_theme_styles(self._theme)
                color = theme_colors[i % len(theme_colors)]
                card = WitnessCard(witness, full_html, color, is_html=True, font_family=self._font_family, font_size=self._font_size)
                self.inner_layout.addWidget(card)

        self.inner_layout.addStretch()
        self.scroll.verticalScrollBar().setValue(0)
