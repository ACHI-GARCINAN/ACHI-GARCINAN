import re
import sys
import os

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QSplitter,
    QPushButton, QLineEdit, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor, QIcon, QKeyEvent

from styles import STYLE
from db import fetch_masechet, fetch_page, fetch_page_words
from utils import _page_matches, _masechet_matches
from widgets.section_block import SectionBlock
from widgets.witness_panel import WitnessPanel
from widgets.touch_scroll import TouchScrollArea
from widgets.copyright_popup import CopyrightPopup
from widgets.words_view import WordsView


def get_base_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_icon() -> QIcon:
    base = get_base_dir()
    for name in ('logo.ico', 'logo.png', 'icon.ico', 'icon.png'):
        path = os.path.join(base, name)
        if os.path.exists(path):
            return QIcon(path)
    return QIcon()


class MainWindow(QMainWindow):
    def __init__(self, masechtot: list):
        super().__init__()
        self.masechtot = masechtot
        self.current_masechet_name = ""
        self.witnesses = []
        self.pages = []
        self.main_witness = ''
        self.current_page_idx = 0
        self.selected_block = None
        self.section_blocks = []
        self._current_words_data = []
        self._current_word_idx = -1

        self.setWindowTitle("סינופסיס תלמוד בבלי")
        self.setMinimumSize(1100, 650)
        self.showMaximized()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(STYLE)
        self.setWindowIcon(get_icon())

        self.display_mode = 'sections'  # 'sections' or 'words'
        self._words_view = None

        self._build_ui()

        if self.masechtot:
            self.masechet_list.setCurrentRow(0)

    def _show_copyright_notice(self):
        popup = CopyrightPopup(self.centralWidget())
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
        main_area.setStyleSheet("background-color:#F0F4F7;")
        ma_layout = QVBoxLayout(main_area)
        ma_layout.setContentsMargins(0, 0, 0, 0)
        ma_layout.setSpacing(0)

        header = QWidget()
        header.setStyleSheet("background-color:#E1E8ED; border-bottom: 1px solid #CBD5E0;")
        h_outer = QHBoxLayout(header)
        h_outer.setContentsMargins(20, 10, 20, 10)
        h_outer.setSpacing(15)

        # Left Side: Mode Toggle and Info Button
        left_layout = QHBoxLayout()
        left_layout.setSpacing(10)
        
        warn_btn = QPushButton("¡")
        warn_btn.setToolTip("הערת שימוש")
        warn_btn.setFixedSize(30, 30)
        warn_btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        warn_btn.setStyleSheet("""
            QPushButton {
                color: #5A6A82;
                background: transparent;
                border: 2px solid #5A6A82;
                border-radius: 15px;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                color: #2D3748;
                border-color: #2D3748;
                background: rgba(90,106,130,0.1);
            }
        """)
        warn_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        warn_btn.clicked.connect(self._show_copyright_notice)
        left_layout.addWidget(warn_btn)

        self.mode_btn = QPushButton("\U0001f520 תצוגת מילים")
        self.mode_btn.setFont(QFont("David", 11))
        self.mode_btn.setFixedHeight(30)
        self.mode_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.mode_btn.setStyleSheet("""
            QPushButton {
                color: #4A5568;
                background: #DDE4E9;
                border: 1px solid #CBD5E0;
                border-radius: 6px;
                padding: 0 12px;
            }
            QPushButton:hover {
                background: #D1D9E0;
                border-color: #A0B4CC;
            }
            QPushButton:checked {
                background: #A0B4CC;
                border-color: #5A6A82;
                color: #2D3748;
            }
        """)
        self.mode_btn.setCheckable(True)
        self.mode_btn.toggled.connect(self._on_mode_toggled)
        left_layout.addWidget(self.mode_btn)
        
        h_outer.addLayout(left_layout)

        # Center: Navigation and Title
        h_outer.addStretch(1)
        
        center_layout = QHBoxLayout()
        center_layout.setSpacing(20)

        self.prev_btn = QPushButton("→")
        self.prev_btn.setFixedSize(35, 35)
        self.prev_btn.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.prev_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.prev_btn.setStyleSheet("""
            QPushButton { color: #5A6A82; background: transparent; border: 1px solid #A0B4CC; border-radius: 17px; }
            QPushButton:hover { background: #DDE4E9; border-color: #5A6A82; color: #2D3748; }
            QPushButton:disabled { color: #CBD5E0; border-color: #E1E8ED; }
        """)
        self.prev_btn.clicked.connect(self._go_prev_page)
        center_layout.addWidget(self.prev_btn)

        titles_widget = QWidget()
        titles_widget.setStyleSheet("background:transparent;")
        titles_vbox = QVBoxLayout(titles_widget)
        titles_vbox.setContentsMargins(0, 0, 0, 0)
        titles_vbox.setSpacing(2)

        self.page_title = QLabel("")
        self.page_title.setFont(QFont("David", 20, QFont.Weight.Bold))
        self.page_title.setStyleSheet("color:#2D3748;background:transparent;")
        self.page_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titles_vbox.addWidget(self.page_title)

        self.page_sub = QLabel("")
        self.page_sub.setFont(QFont("Arial", 10))
        self.page_sub.setStyleSheet("color:#718096;background:transparent;")
        self.page_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titles_vbox.addWidget(self.page_sub)
        
        center_layout.addWidget(titles_widget)

        self.next_btn = QPushButton("←")
        self.next_btn.setFixedSize(35, 35)
        self.next_btn.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.next_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.next_btn.setStyleSheet("""
            QPushButton { color: #5A6A82; background: transparent; border: 1px solid #A0B4CC; border-radius: 17px; }
            QPushButton:hover { background: #DDE4E9; border-color: #5A6A82; color: #2D3748; }
            QPushButton:disabled { color: #CBD5E0; border-color: #E1E8ED; }
        """)
        self.next_btn.clicked.connect(self._go_next_page)
        center_layout.addWidget(self.next_btn)
        
        h_outer.addLayout(center_layout)
        h_outer.addStretch(1)

        # Right Side: Search Box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText('חפש מסכת ודף...')
        self.search_box.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.search_box.setFont(QFont('David', 12))
        self.search_box.setFixedWidth(200)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #F0F4F7;
                color: #2D3748;
                border: 1px solid #CBD5E0;
                border-radius: 6px;
                padding: 5px 10px;
                selection-background-color: #A0B4CC;
            }
            QLineEdit:focus {
                border: 1px solid #5A6A82;
                background-color: #FFFFFF;
            }
            QLineEdit::placeholder {
                color: #A0AEC0;
            }
        """)
        self.search_box.returnPressed.connect(self._quick_nav)
        h_outer.addWidget(self.search_box)

        ma_layout.addWidget(header)

        self.text_scroll = TouchScrollArea()
        self.text_scroll.setWidgetResizable(True)
        self.text_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_scroll.setStyleSheet("QScrollArea{border:none;background:#F0F4F7;}")

        self.text_container = QWidget()
        self.text_container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.text_container.setStyleSheet("background-color:#F0F4F7;")
        self.text_layout = QVBoxLayout(self.text_container)
        self.text_layout.setContentsMargins(12, 14, 12, 30)
        self.text_layout.setSpacing(8)
        self.text_layout.addStretch()

        self.text_scroll.setWidget(self.text_container)
        ma_layout.addWidget(self.text_scroll, 1)

        page_panel = QWidget()
        page_panel.setStyleSheet("background-color:#E1E8ED; border-left: 1px solid #CBD5E0;")
        pp_layout = QVBoxLayout(page_panel)
        pp_layout.setContentsMargins(0, 0, 0, 0)
        pp_layout.setSpacing(0)

        pg_hdr = QLabel("דפים")
        pg_hdr.setFont(QFont("Arial", 10))
        pg_hdr.setStyleSheet("color:#4A5568;padding:10px 6px 8px 6px;letter-spacing:2px;border-bottom:1px solid #D1D9E0;")
        pg_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pp_layout.addWidget(pg_hdr)

        self.page_list = QListWidget()
        self.page_list.setObjectName("page_list")
        self.page_list.setFont(QFont("David", 14))
        self.page_list.setFixedWidth(85)
        self.page_list.currentRowChanged.connect(self._load_page)
        pp_layout.addWidget(self.page_list, 1)

        masechet_panel = QWidget()
        masechet_panel.setStyleSheet("background-color:#D9E1E8; border-left: 1px solid #CBD5E0;")
        mp_layout = QVBoxLayout(masechet_panel)
        mp_layout.setContentsMargins(0, 0, 0, 0)
        mp_layout.setSpacing(0)

        ms_hdr = QLabel("מסכתות")
        ms_hdr.setFont(QFont("Arial", 10))
        ms_hdr.setStyleSheet("color:#4A5568;padding:10px 6px 8px 6px;letter-spacing:2px;border-bottom:1px solid #243424;")
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

    def _go_prev_page(self):
        row = self.page_list.currentRow()
        if row > 0:
            self.page_list.setCurrentRow(row - 1)

    def _go_next_page(self):
        row = self.page_list.currentRow()
        if row < self.page_list.count() - 1:
            self.page_list.setCurrentRow(row + 1)

    def _update_nav_buttons(self, idx: int):
        self.prev_btn.setEnabled(idx > 0)
        self.next_btn.setEnabled(idx < self.page_list.count() - 1)
        # Hide/Show logic as requested
        self.prev_btn.setVisible(idx > 0)
        self.next_btn.setVisible(idx < self.page_list.count() - 1)

    def _quick_nav(self):
        raw = self.search_box.text().strip()
        if not raw:
            return

        m = re.match(
            r'^([\u05d0-\u05ea]+(?:\s[\u05d0-\u05ea]+)*)'
            r'(?:\s+\u05d3\u05e3)?'
            r'\s+([\u05d0-\u05ea"\u05f4\u05f3\u2019\']+|\d+)$',
            raw
        )
        if not m:
            self._search_error()
            return

        ms_query = m.group(1).strip()
        pg_query = m.group(2).strip()

        ms_idx = next((i for i, ms in enumerate(self.masechtot)
                       if _masechet_matches(ms['name'], ms_query)), None)
        if ms_idx is None:
            self._search_error()
            return

        if self.masechet_list.currentRow() != ms_idx:
            self.masechet_list.setCurrentRow(ms_idx)

        pg_idx = next((i for i, pg in enumerate(self.pages)
                       if _page_matches(pg['page'], pg_query)), None)
        if pg_idx is None:
            self._search_error()
            return

        self.page_list.setCurrentRow(pg_idx)
        self.search_box.clear()
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #3A2418; color: #FFF5E6;
                border: 1px solid #6A4020; border-radius: 6px;
                padding: 5px 10px; selection-background-color: #7A3810;
            }
            QLineEdit:focus { border: 1px solid #C8A060; background-color: #4A2E1A; }
        """)

    def _search_error(self):
        self.search_box.setStyleSheet(
            self.search_box.styleSheet() + 'QLineEdit { border: 1px solid #CC3300; }'
        )

    def _load_masechet(self, idx: int):
        if idx < 0 or idx >= len(self.masechtot):
            return
        ms = self.masechtot[idx]
        try:
            witnesses, pages = fetch_masechet(ms['id'])
        except Exception as e:
            self.page_title.setText(f"Error: {e}")
            return

        self.witnesses = witnesses
        self.pages = pages
        self.current_masechet_name = ms['name']
        self.main_witness = witnesses[0] if witnesses else ''
        self.selected_block = None
        self.section_blocks = []
        self._words_view = None
        self.witness_panel.update_witnesses(witnesses)
        self.witness_panel.reset()
        self.page_sub.setText(f"טקסט: {self.main_witness}" if self.main_witness else "")

        self.page_list.blockSignals(True)
        self.page_list.clear()
        for pg in pages:
            item = QListWidgetItem(pg['page'])
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.page_list.addItem(item)
        self.page_list.blockSignals(False)

        self._clear_text()
        self.page_title.setText(self.current_masechet_name)
        if pages:
            self.page_list.setCurrentRow(0)

    def _load_page(self, idx: int):
        if idx < 0 or idx >= len(self.pages):
            return
        self.current_page_idx = idx
        self.selected_block = None
        self.section_blocks = []
        self._words_view = None
        page = self.pages[idx]
        self.page_title.setText(f"{self.current_masechet_name} · דף {page['page']}")
        self._update_nav_buttons(idx)
        self._clear_text()

        sections = fetch_page(page['_id'])

        if self.display_mode == 'words':
            self._load_page_words(page, sections)
        else:
            self._load_page_sections(sections, page['page'])

        self.text_scroll.verticalScrollBar().setValue(0)
        self.witness_panel.reset()

    def _load_page_sections(self, sections: list, page_label: str):
        for section in sections:
            block = SectionBlock(section, self.main_witness)
            block.clicked.connect(
                lambda checked=False, s=section, b=block, p=page_label:
                    self._select_section(s, b, p)
            )
            self.text_layout.insertWidget(self.text_layout.count() - 1, block)
            self.section_blocks.append(block)

    def _load_page_words(self, page: dict, sections: list):
        words_data = fetch_page_words(page['_id'])
        self._current_words_data = words_data
        self._current_word_idx = -1
        if not words_data:
            lbl = QLabel("אין נתוני מילים לדף זה")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color:#A09080;font-size:14px;padding:40px;")
            self.text_layout.insertWidget(self.text_layout.count() - 1, lbl)
            return

        wv = WordsView(words_data, self.main_witness)
        wv.word_clicked.connect(
            lambda idx, p=page['page'], wd=words_data: self._select_word(idx, wd, p)
        )
        self._words_view = wv
        self.text_layout.insertWidget(self.text_layout.count() - 1, wv)

    def _select_word(self, idx: int, words_data: list, page: str):
        self._current_word_idx = idx
        if self._words_view:
            self._words_view.select_word(idx)
        self.witness_panel.show_word(
            words_data[idx], page, self.main_witness,
            words_data=words_data, word_idx=idx
        )

    def _on_mode_toggled(self, checked: bool):
        self.display_mode = 'words' if checked else 'sections'
        if checked:
            self.mode_btn.setText("\U0001f4dc תצוגת קטעים")
        else:
            self.mode_btn.setText("\U0001f520 תצוגת מילים")
        if self.pages:
            self._load_page(self.current_page_idx)

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
        if not self.selected_block:
            return
        self.selected_block.show_witness_diff(witness_name)

    def keyPressEvent(self, event: QKeyEvent):
        """חץ שמאלה = מילה הבאה, חץ ימינה = מילה הקודמת (RTL)."""
        if self.display_mode == 'words' and self._current_words_data:
            key = event.key()
            if key == Qt.Key.Key_Left:
                # אם אין מילה נבחרת — התחל מהמילה הראשונה
                if self._current_word_idx < 0:
                    new_idx = 0
                else:
                    new_idx = self._current_word_idx + 1
            elif key == Qt.Key.Key_Right:
                # אם אין מילה נבחרת — התחל מהמילה האחרונה
                if self._current_word_idx < 0:
                    new_idx = len(self._current_words_data) - 1
                else:
                    new_idx = self._current_word_idx - 1
            else:
                super().keyPressEvent(event)
                return
            new_idx = max(0, min(new_idx, len(self._current_words_data) - 1))
            if new_idx != self._current_word_idx:
                page = self.pages[self.current_page_idx]['page']
                self._select_word(new_idx, self._current_words_data, page)
            return
        super().keyPressEvent(event)
