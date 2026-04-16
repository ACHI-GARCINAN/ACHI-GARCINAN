from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QCheckBox,
    QFrame, QSizePolicy, QGraphicsDropShadowEffect, QTextBrowser
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from styles import WITNESS_COLORS
from widgets.witness_card import WitnessCard


def normalize_word(w: str) -> str:
    import re
    if not w: return ""
    w = re.sub(r'[\u05B0-\u05C7]', '', w)
    w = re.sub(r'[\u05f3\u05f4",.\-:;!?()\[\]]', '', w)
    return w.strip()


class WitnessPanel(QWidget):
    witness_clicked = pyqtSignal(str)

    def __init__(self, witnesses: list, parent=None):
        super().__init__(parent)
        self.witnesses = witnesses
        self.highlight_diffs = False
        self.hide_empty_witnesses = True
        
        # State for re-rendering
        self._current_section = None
        self._current_page = ''
        self._base_text = ''
        self._word_mode = False
        self._words_data = None
        self._word_idx = -1
        self._main_witness = ''

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet("background-color:#F0F4F7;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header_widget = QWidget()
        header_widget.setStyleSheet("background-color:#E1E8ED;border-bottom:2px solid #A0B4CC;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 10, 16, 8)
        header_layout.setSpacing(5)

        self.header = QLabel("בחר קטע לעדי נוסח")
        self.header.setFont(QFont("David", 14, QFont.Weight.Bold))
        self.header.setStyleSheet("color:#2D3748;background:transparent;border:none;")
        self.header.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.header)

        self.highlight_cb = QCheckBox("הדגש שינויים מוילנא")
        self.highlight_cb.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.highlight_cb.setFont(QFont("Arial", 10))
        self.highlight_cb.setChecked(False)
        self.highlight_cb.stateChanged.connect(self._on_highlight_changed)
        header_layout.addWidget(self.highlight_cb, alignment=Qt.AlignmentFlag.AlignRight)

        self.hide_empty_cb = QCheckBox("הסתר עדי נוסח ריקים")
        self.hide_empty_cb.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.hide_empty_cb.setFont(QFont("Arial", 10))
        self.hide_empty_cb.setChecked(True)
        self.hide_empty_cb.stateChanged.connect(self._on_hide_empty_changed)
        header_layout.addWidget(self.hide_empty_cb, alignment=Qt.AlignmentFlag.AlignRight)

        self.hint_label = QLabel("לחץ על קטע כדי לראות את השינויים בטקסט המרכזי")
        self.hint_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.hint_label.setFont(QFont("Arial", 9))
        self.hint_label.setStyleSheet("color:#718096;background:transparent;border:none;font-style:italic;")
        self.hint_label.setVisible(False)
        header_layout.addWidget(self.hint_label, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(header_widget)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea{border:none;background:#F0F4F7;}")

        self.container = QWidget()
        self.container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.container.setStyleSheet("background-color:#F0F4F7;")
        self.inner_layout = QVBoxLayout(self.container)
        self.inner_layout.setContentsMargins(4, 10, 4, 20)
        self.inner_layout.setSpacing(4)

        self._show_placeholder()

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

    def update_witnesses(self, witnesses: list):
        self.witnesses = witnesses

    def _on_highlight_changed(self, state):
        # Handle both int (from signal) and bool
        if isinstance(state, int):
            self.highlight_diffs = (state == Qt.CheckState.Checked.value or state == 2)
        else:
            self.highlight_diffs = bool(state)
            
        self.hint_label.setVisible(self.highlight_diffs and not self._word_mode)
        if self._word_mode and self._words_data is not None:
            self.show_word(self._current_section, self._current_page, self._main_witness,
                           words_data=self._words_data, word_idx=self._word_idx)
        elif self._current_section is not None:
            self.show_section(self._current_section, self._current_page, self._base_text)

    def _on_hide_empty_changed(self, state):
        if isinstance(state, int):
            self.hide_empty_witnesses = (state == Qt.CheckState.Checked.value or state == 2)
        else:
            self.hide_empty_witnesses = bool(state)
            
        if self._word_mode and self._words_data is not None:
            self.show_word(self._current_section, self._current_page, self._main_witness,
                           words_data=self._words_data, word_idx=self._word_idx)
        elif self._current_section is not None:
            self.show_section(self._current_section, self._current_page, self._base_text)

    def _show_placeholder(self):
        ph = QLabel("←  לחץ על קטע בטקסט\nכדי לראות את עדי הנוסח")
        ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph.setStyleSheet("color:#718096;font-size:14px;padding:50px 20px;background:transparent;")
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

    def show_section(self, section: dict, page: str, base_text: str = ''):
        self._current_section = section
        self._current_page = page
        self._base_text = base_text
        self._word_mode = False
        self._words_data = None
        self._word_idx = -1
        self._clear()

        self.header.setText(f"דף {page}  ·  {section['section']}")

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

    def show_word(self, word_entry: dict, page: str, main_witness: str,
                  words_data: list = None, word_idx: int = -1):
        """מציג את עדי הנוסח למילה בודדת עם הקשר של 12 מילים לפני ואחרי."""
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

        self.header.setText(f"דף {page}  ·  {section_label}  ·  מילה: {main_text or '—'}")

        CONTEXT = 12
        vilna_word = (word_entry['witnesses'].get(main_witness) or '').strip()
        if vilna_word == 'None':
            vilna_word = ''

        for i, witness in enumerate(self.witnesses):
            if words_data is not None and word_idx >= 0:
                before_parts = []
                for j in range(max(0, word_idx - CONTEXT), word_idx):
                    t = words_data[j]['witnesses'].get(witness) or ''
                    if t == 'None':
                        t = ''
                    before_parts.append(t if t else '—')

                sel_text = words_data[word_idx]['witnesses'].get(witness) or ''
                if sel_text == 'None':
                    sel_text = ''
                selected_word = sel_text if sel_text else '—'

                after_parts = []
                for j in range(word_idx + 1, min(len(words_data), word_idx + CONTEXT + 1)):
                    t = words_data[j]['witnesses'].get(witness) or ''
                    if t == 'None':
                        t = ''
                    after_parts.append(t if t else '—')

                # Check if this witness has any text in the context window
                has_any_in_context = bool(sel_text) or any(
                    (words_data[j]['witnesses'].get(witness) or '').strip() not in ('', 'None')
                    for j in range(max(0, word_idx - CONTEXT), min(len(words_data), word_idx + CONTEXT + 1))
                )
                
                if not has_any_in_context and self.hide_empty_witnesses:
                    continue

                is_vilna = (witness == main_witness)
                if self.highlight_diffs and not is_vilna:
                    norm_sel = normalize_word(sel_text)
                    norm_vil = normalize_word(vilna_word)
                    word_differs = bool(sel_text) and (norm_sel != norm_vil)
                    if word_differs:
                        highlight_style = (
                            "background-color:#E53E3E;"
                            "color:#FFFFFF;"
                            "border-radius:3px;"
                            "padding:0 3px;"
                            "font-weight:600;"
                        )
                    else:
                        highlight_style = (
                            "background-color:#FFD700;"
                            "color:#1A202C;"
                            "border-radius:3px;"
                            "padding:0 3px;"
                            "font-weight:600;"
                        )
                else:
                    highlight_style = (
                        "background-color:#FFD700;"
                        "color:#1A202C;"
                        "border-radius:3px;"
                        "padding:0 3px;"
                        "font-weight:600;"
                    )
                
                highlighted_word = f'<span style="{highlight_style}">{selected_word}</span>'

                before_html = ' '.join(before_parts)
                after_html = ' '.join(after_parts)
                context_html = ''
                if before_html:
                    context_html += before_html + ' '
                context_html += highlighted_word
                if after_html:
                    context_html += ' ' + after_html

                color = WITNESS_COLORS[i % len(WITNESS_COLORS)]
                accent, bg = color

                card_frame = QFrame()
                card_frame.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                
                # Check if current word exists
                has_current = bool(sel_text) and sel_text != '—'
                
                if has_any_in_context:
                    card_frame.setStyleSheet(
                        f"QFrame{{background-color:{bg};"
                        f"border:1px solid {accent}35;"
                        f"border-top:3px solid {accent};"
                        f"border-radius:10px;margin:4px 8px;}}"
                    )
                else:
                    card_frame.setStyleSheet(
                        "QFrame{background-color:#F0EDE6;"
                        "border:1px dashed #C5B89A;"
                        "border-radius:10px;margin:4px 8px;}"
                    )
                card_layout = QVBoxLayout(card_frame)
                card_layout.setContentsMargins(14, 10, 14, 12)
                card_layout.setSpacing(6)

                name_lbl = QLabel(witness)
                name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
                name_lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                if has_any_in_context:
                    name_lbl.setStyleSheet(
                        f"color:{accent};background:transparent;"
                        f"border:1px solid {accent};border-radius:5px;padding:3px 8px;"
                    )
                else:
                    name_lbl.setStyleSheet(
                        "color:#A09080;background:transparent;"
                        "border:1px solid #C5B89A;border-radius:5px;padding:3px 8px;"
                    )
                card_layout.addWidget(name_lbl)

                if has_any_in_context:
                    txt_browser = QTextBrowser()
                    txt_browser.setOpenLinks(False)
                    txt_browser.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                    txt_browser.setHtml(
                        f'<div dir="rtl" style="font-family:David,serif;font-size:15pt;'
                        f'color:#1A0A00;text-align:right;">{context_html}</div>'
                    )
                    txt_browser.setStyleSheet(
                        "QTextBrowser{background:transparent;border:none;color:#1A0A00;}"
                    )
                    txt_browser.setSizePolicy(
                        QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
                    )
                    txt_browser.document().adjustSize()
                    h = int(txt_browser.document().size().height()) + 16
                    txt_browser.setFixedHeight(max(50, h))
                    card_layout.addWidget(txt_browser)
                else:
                    miss = QLabel("אין עד נוסח לקטע זה")
                    miss.setAlignment(Qt.AlignmentFlag.AlignRight)
                    miss.setStyleSheet(
                        "color:#B0A090;font-style:italic;font-size:12px;background:transparent;"
                    )
                    card_layout.addWidget(miss)

                shadow = QGraphicsDropShadowEffect()
                shadow.setBlurRadius(8)
                shadow.setColor(QColor(0, 0, 0, 18))
                shadow.setOffset(0, 2)
                card_frame.setGraphicsEffect(shadow)

                self.inner_layout.addWidget(card_frame)

            else:
                # fallback for missing words_data
                text = word_entry.get('witnesses', {}).get(witness)
                if text == 'None' or text == '':
                    text = None
                if text is None and self.hide_empty_witnesses:
                    continue
                color = WITNESS_COLORS[i % len(WITNESS_COLORS)]
                card = WitnessCard(witness, text, color, base_text='', highlight=False, clickable=False)
                self.inner_layout.addWidget(card)

        self.inner_layout.addStretch()
        self.scroll.verticalScrollBar().setValue(0)

    def reset(self):
        self._current_section = None
        self._current_page = ''
        self._base_text = ''
        self._word_mode = False
        self._words_data = None
        self._word_idx = -1
        self._main_witness = ''
        self._clear()
        self.header.setText("בחר קטע לעדי נוסח")
        self._show_placeholder()
