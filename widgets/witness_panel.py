import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QCheckBox,
    QFrame, QSizePolicy, QTextBrowser, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from settings_manager import load_settings, save_settings
from styles import get_theme_styles, get_theme_config
from witness_card import WitnessCard
from touch_scroll import TouchScrollArea
from manuscript_info_popup import ManuscriptInfoPopup
from utils import normalize_word
from db import fetch_manuscript_info
from icons import get_theme_icon, IconName

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
        self.show_summary = _saved.get('show_summary', False)
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
        self.header_layout.setContentsMargins(16, 8, 16, 6)
        self.header_layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.header_label = QLabel("בחר קטע לעדי נוסח")
        self.header_label.setFont(QFont("David", 13, QFont.Weight.Bold))
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        top_row.addWidget(self.header_label, 1)

        self._options_visible = False
        self.options_toggle_btn = QPushButton()
        self.options_toggle_btn.setIcon(get_theme_icon(IconName.OPTIONS, self._theme, 16)) 
        self.options_toggle_btn.setFixedSize(24, 24)
        self.options_toggle_btn.setToolTip("אפשרויות תצוגה")
        self.options_toggle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.options_toggle_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;color:#888;}"
            "QPushButton:hover{color:#333;}"
        )
        self.options_toggle_btn.clicked.connect(self._toggle_options)
        top_row.addWidget(self.options_toggle_btn)  # <--- תוודא שכתוב btn וסגור סוגריים
        self.header_layout.addLayout(top_row)
        
        self.options_widget = QWidget()
        self.options_widget.setVisible(False)
        opts_layout = QVBoxLayout(self.options_widget)
        opts_layout.setContentsMargins(0, 2, 0, 2)
        opts_layout.setSpacing(3)

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

        opts_layout.addWidget(self.highlight_cb)
        opts_layout.addWidget(self.hide_empty_cb)
        opts_layout.addWidget(self.hide_minor_cb)

        self.show_summary_cb = QCheckBox("הצג סיכום")
        self.show_summary_cb.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.show_summary_cb.setFont(QFont("Arial", 10))
        self.show_summary_cb.setChecked(self.show_summary)
        self.show_summary_cb.stateChanged.connect(self._on_show_summary_changed)
        opts_layout.addWidget(self.show_summary_cb)

        self.header_layout.addWidget(self.options_widget)

        self.hint_label = QLabel("לחץ על קטע כדי לראות את השינויים בטקסט המרכזי")
        self.hint_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.hint_label.setFont(QFont("Arial", 9))
        self.hint_label.setVisible(False)
        self.header_layout.addWidget(self.hint_label)

        self.main_layout.addWidget(self.header_widget)
        self.scroll = TouchScrollArea()
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
        self.show_summary_cb.setStyleSheet(cb_style)
        
    def _toggle_options(self):
        self._options_visible = not self._options_visible
        self.options_widget.setVisible(self._options_visible)
        icon_name = IconName.CLOSE if self._options_visible else IconName.OPTIONS
        self.options_toggle_btn.setIcon(get_theme_icon(icon_name, self._theme, 16))
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

    def _on_show_summary_changed(self, state):
        if isinstance(state, int):
            self.show_summary = (state == 2)
        else:
            self.show_summary = bool(state)
        save_settings({'show_summary': self.show_summary})
        if self._word_mode and self._words_data is not None:
            self.show_word(self._current_section, self._current_page, self._main_witness,
                           words_data=self._words_data, word_idx=self._word_idx)

    def _is_print_witness(self, witness_name: str) -> bool:
        """בודק אם עד הנוסח הוא דפוס (יש בסוגריים אותיות עבריות וגרשיים)."""
        import re
        m = re.search(r'\(([^)]+)\)', witness_name)
        if not m:
            return False
        inside = m.group(1)
        has_heb = bool(re.search(r'[א-ת]', inside))
        has_quote = bool(re.search(r'["\u05f4\u05f3\'״]', inside))
        return has_heb and has_quote

    def _build_summary_card(self, word_entry: dict, main_witness: str,
                             words_data: list, word_idx: int) -> QWidget:
        """בונה כרטיסיית סיכום עבור מילה בתצוגת מילים."""
        from PyQt6.QtWidgets import QFrame
        cfg = get_theme_config(self._theme)

        vilna_word = (word_entry['witnesses'].get(main_witness) or '').strip()
        if vilna_word == 'None':
            vilna_word = ''

        CONTEXT = 12

        # איסוף נתוני כל עד נוסח (תוך התעלמות מעדים ריקים כמו "הסתר עדי נוסח ריקים")
        variant_map = {}  # text -> [witness_names]

        for i, witness in enumerate(self.witnesses):
            if i == 0:
                continue
            sel_text = (words_data[word_idx]['witnesses'].get(witness) or '').strip()
            if sel_text == 'None':
                sel_text = ''

            # בדוק אם יש תוכן כלשהו בהקשר (כמו לוגיקת hide_empty)
            has_any_in_context = bool(sel_text) or any(
                (words_data[j]['witnesses'].get(witness) or '').strip() not in ('', 'None')
                for j in range(max(0, word_idx - CONTEXT), min(len(words_data), word_idx + CONTEXT + 1))
            )
            if not has_any_in_context:
                continue  # דלג על עדים ריקים לחלוטין

            key = sel_text if sel_text else '—'
            variant_map.setdefault(key, []).append(witness)

        if not variant_map:
            summary_text = "אינו קיים בכל עדי הנוסח"
        else:
            all_absent = all(k == '—' for k in variant_map)
            norm_vilna = normalize_word(vilna_word)
            all_same = all(normalize_word(k) == norm_vilna for k in variant_map if k != '—') and '—' not in variant_map

            if all_absent:
                summary_text = "אינו קיים בכל עדי הנוסח"
            elif all_same and len(variant_map) == 1:
                summary_text = "אין שינוי בכל עדי הנוסח"
            else:
                parts = []
                sorted_variants = sorted(variant_map.items(), key=lambda x: -len(x[1]))
                for text, witnesses_list in sorted_variants:
                    n_print = sum(1 for w in witnesses_list if self._is_print_witness(w))
                    n_ms = len(witnesses_list) - n_print

                    # אם יש רק עד אחד ואין בשמו אותיות אנגליות — כתוב את שמו
                    has_english = bool(__import__('re').search(r'[A-Za-z]', witnesses_list[0]))
                    use_name = (len(witnesses_list) == 1 and not has_english)
                    if use_name:
                        name_str = witnesses_list[0]
                    else:
                        counts = []
                        if n_print > 0:
                            counts.append(f"{n_print} דפוסים")
                        if n_ms > 0:
                            counts.append(f"{n_ms} כתבי יד")
                        count_str = " ו".join(counts)

                    norm_text = normalize_word(text) if text != '—' else ''
                    if use_name:
                        if text == '—':
                            variant_desc = f"{name_str}: אינו קיים"
                        elif norm_text == norm_vilna:
                            variant_desc = f"{name_str}: אין שינוי"
                        else:
                            variant_desc = f"{name_str}: <b>{text}</b>"
                    else:
                        if text == '—':
                            variant_desc = f"ב{count_str} אינו קיים"
                        elif norm_text == norm_vilna:
                            variant_desc = f"ב{count_str} אין שינוי"
                        else:
                            variant_desc = f"ב{count_str} הנוסח <b>{text}</b>"
                    parts.append(variant_desc)
                summary_text = "  |  ".join(parts)

        # יצירת הווידג'ט
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        card.setStyleSheet(
            f"QFrame {{ background: {cfg.get('panel_header_bg', '#EEF2FF')};"
            f" border: 2px solid {cfg.get('panel_header_border', '#6366F1')};"
            f" border-radius: 6px; margin: 2px; }}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 6, 10, 6)
        card_layout.setSpacing(2)

        title_lbl = QLabel("סיכום")
        title_lbl.setFont(QFont("David", 11, QFont.Weight.Bold))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        title_lbl.setStyleSheet(f"color: {cfg.get('panel_header_text', '#4338CA')}; background: transparent; border: none;")
        card_layout.addWidget(title_lbl)

        text_lbl = QLabel(summary_text)
        text_lbl.setFont(QFont("David", 10))
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        text_lbl.setWordWrap(True)
        text_lbl.setTextFormat(Qt.TextFormat.RichText)
        text_lbl.setStyleSheet(f"color: {cfg.get('panel_header_text', '#374151')}; background: transparent; border: none;")
        card_layout.addWidget(text_lbl)

        return card

    def _show_placeholder(self):
        self._clear()
        cfg = get_theme_config(self._theme)
        self.inner_layout.addStretch()

        icon = QLabel("📖")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size:36px;background:transparent;padding:0;")

        title = QLabel("בחרו קטע לעדי הנוסח")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("David", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{cfg['panel_header_text']};background:transparent;")

        subtitle = QLabel("לחיצה על קטע בטקסט המרכזי\nתציג כאן את כל עדי הנוסח")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("David", 11))
        subtitle.setStyleSheet(f"color:{cfg['panel_hint_text']};background:transparent;font-style:italic;padding:4px 20px;")

        self.inner_layout.addWidget(icon)
        self.inner_layout.addWidget(title)
        self.inner_layout.addWidget(subtitle)
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
                continue
            text = witness_data.get(witness)
            if text == 'None' or text == '':
                text = None
            if text is None and self.hide_empty_witnesses:
                continue
            color = theme_colors[i % len(theme_colors)]
            
            # בדוק אם יש מידע על כתב יד
            manuscript_info = fetch_manuscript_info(witness)
            has_manuscript = manuscript_info is not None
            
            card = WitnessCard(
                witness, text, color,
                base_text=base_text,
                highlight=self.highlight_diffs,
                clickable=self.highlight_diffs,
                font_family=self._font_family,
                font_size=self._font_size,
                hide_minor=self.hide_minor_diffs,
                has_manuscript_info=has_manuscript
            )
            if self.highlight_diffs and text:
                card.clicked.connect(self.witness_clicked.emit)
            if has_manuscript:
                card.manuscript_requested.connect(self._on_manuscript_requested)
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

        # כרטיסיית סיכום (רק בתצוגת מילים, אם הופעלה)
        if self.show_summary and words_data is not None and word_idx >= 0:
            summary_card = self._build_summary_card(word_entry, main_witness, words_data, word_idx)
            self.inner_layout.addWidget(summary_card)

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
                    from utils import is_minor_diff, is_acronym_minor_diff
                    norm_sel = normalize_word(sel_text)
                    norm_vil = normalize_word(vilna_word)
                    # שינוי: גם כשיש מילה בוילנא אבל אין בעד הנוסח (קו) - זה שינוי
                    missing_in_witness = bool(vilna_word) and not bool(sel_text)
                    word_differs = missing_in_witness or (bool(sel_text) and (norm_sel != norm_vil))
                    if word_differs and not missing_in_witness and self.hide_minor_diffs:
                        if is_minor_diff(sel_text, vilna_word):
                            word_differs = False
                        # כלל ראשי תיבות: בדוק אם המילה הנוכחית + שכנותיה הן ר"ת של הצד השני
                        if word_differs and words_data is not None:
                            # אסוף את המילים השלמות סביב המיקום הנוכחי בכל צד
                            def _get_context_words(witness_name, center_idx, n=3):
                                words = []
                                for j in range(center_idx, min(len(words_data), center_idx + n)):
                                    t = (words_data[j]['witnesses'].get(witness_name) or '').strip()
                                    if t and t != 'None':
                                        words.append(t)
                                return words
                            wit_context = _get_context_words(witness, word_idx)
                            vil_context = _get_context_words(main_witness, word_idx)
                            if (is_acronym_minor_diff(
                                    wit_context[:1] if wit_context else [sel_text],
                                    vil_context)
                                or is_acronym_minor_diff(
                                    wit_context,
                                    vil_context[:1] if vil_context else [vilna_word])):
                                word_differs = False
                    if word_differs:
                        if missing_in_witness:
                            # מקף (מילה חסרה בעד הנוסח) — שחור עם הצללה ורדרדה בהירה
                            highlight_style = "color: #1A1A1A; background-color: #FFE4E4; padding: 1px 4px; border-radius: 3px;"
                        else:
                            highlight_style = "color: #E53E3E; font-weight: bold;"
                        selected_word = f'<span style="{highlight_style}">{selected_word}</span>'

                before_str = " ".join(before_parts)
                after_str = " ".join(after_parts)
                full_html = f'<div dir="rtl" style="font-family:{self._font_family},serif; font-size:{self._font_size}pt; line-height:1.4; text-align:left;">'
                full_html += f'<span style="color:#888888;">{before_str}</span> '
                # שינוי: המילה המקבילה תמיד תהיה בצבע שחור (למעט כשיש שינוי אדום) לשיפור קריאות במצב כהה
                word_color = "black" if "<span" not in str(selected_word) else ""
                style_attr = f' style="color:{word_color};"' if word_color else ""
                full_html += f'<b{style_attr}>{selected_word}</b> '
                full_html += f'<span style="color:#888888;">{after_str}</span>'
                full_html += '</div>'

                _, theme_colors = get_theme_styles(self._theme)
                color = theme_colors[i % len(theme_colors)]
                
                # בדוק אם יש מידע על כתב יד
                manuscript_info = fetch_manuscript_info(witness)
                has_manuscript = manuscript_info is not None
                
                card = WitnessCard(witness, full_html, color, is_html=True, font_family=self._font_family, font_size=self._font_size, has_manuscript_info=has_manuscript)
                if has_manuscript:
                    card.manuscript_requested.connect(self._on_manuscript_requested)
                self.inner_layout.addWidget(card)

        self.inner_layout.addStretch()
        self.scroll.verticalScrollBar().setValue(0)


    def _on_manuscript_requested(self, witness_name: str):
        """
        טיפול בבקשה לפתיחת מידע על כתב יד.
        """
        manuscript_info = fetch_manuscript_info(witness_name)
        if manuscript_info:
            popup = ManuscriptInfoPopup(
                manuscript_info['name'],
                manuscript_info['full_text'],
                self.window() if self.window() else self
            )
            popup.exec()
