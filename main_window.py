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

from styles import STYLE, get_theme_styles, get_theme_config
from db import fetch_masechet, fetch_page, fetch_page_words
from utils import _page_matches, _masechet_matches
from widgets.section_block import SectionBlock
from widgets.witness_panel import WitnessPanel
from widgets.touch_scroll import TouchScrollArea
from widgets.copyright_popup import CopyrightPopup
from widgets.words_view import WordsView
from widgets.settings_dialog import SettingsDialog
from settings_manager import load_settings, save_settings


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
        self._page_search_term = ''
        self._page_search_idx = -1

        # טען הגדרות
        settings = load_settings()
        self._font_family = settings['font_family']
        self._font_size = settings['font_size']
        self._theme = settings.get('theme', 'classic')
        self.setWindowTitle("סינופסיס תלמוד בבלי")
        self.setMinimumSize(1100, 650)
        self.showMaximized()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # החל עיצוב לפי ערכת הנושא
        style_str, _ = get_theme_styles(self._theme)
        self.setStyleSheet(style_str)
        
        self.setWindowIcon(get_icon())

        self.display_mode = 'sections'  # 'sections' or 'words'
        self._words_view = None

        self._build_ui()

        if self.masechtot:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.masechet_list.setCurrentRow(0))
            
    def _show_copyright_notice(self):
        popup = CopyrightPopup(self.centralWidget())
        popup.exec()

    def _open_settings(self):
        dlg = SettingsDialog(self._font_family, self._font_size, self._theme, self)
        dlg.settings_changed.connect(self._apply_settings)
        dlg.exec()

    def _apply_settings(self, font_family: str, font_size: int, theme: str):
        self._font_family = font_family
        self._font_size = font_size
        theme_changed = (self._theme != theme)
        self._theme = theme
        
        # שמור להגדרות
        save_settings({
            'font_family': font_family, 
            'font_size': font_size,
            'theme': theme
        })
        
        # עדכן עיצוב אם ערכת הנושא השתנתה
        if theme_changed:
            style_str, _ = get_theme_styles(theme)
            self.setStyleSheet(style_str)
            self._update_ui_colors()
            # רענון הדף הנוכחי כדי להחיל צבעים חדשים
            if self.pages:
                self._load_page(self.current_page_idx)
        
        # עדכן גופן בפאנל עדי הנוסח
        self.witness_panel.update_font(font_family, font_size, theme=self._theme)
        # עדכן גופן בקטעים הנוכחיים
        for block in self.section_blocks:
            block.update_font(font_family, font_size, theme=self._theme)
        # עדכן גופן בתצוגת מילים
        if self._words_view:
            self._words_view.update_font(font_family, font_size, theme=self._theme)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(2)
        root.addWidget(self.splitter)
        self.witness_panel = WitnessPanel([], self._font_family, self._font_size, theme=self._theme)
        self.witness_panel.setMinimumWidth(280)
        self.witness_panel.witness_clicked.connect(self._on_witness_card_clicked)

        self.main_area = QWidget()
        self.ma_layout = QVBoxLayout(self.main_area)
        self.ma_layout.setContentsMargins(0, 0, 0, 0)
        self.ma_layout.setSpacing(0)

        self.header = QWidget()
        self.h_outer = QHBoxLayout(self.header)
        self.h_outer.setContentsMargins(20, 10, 20, 10)
        self.h_outer.setSpacing(15)

        # Left Side: Mode Toggle, Info Button, Settings Button
        left_layout = QHBoxLayout()
        left_layout.setSpacing(10)

        self.hamburger_btn = QPushButton("▶")
        self.hamburger_btn.setToolTip("הצג/הסתר ניווט")
        self.hamburger_btn.setFixedSize(30, 30)
        self.hamburger_btn.setFont(QFont("Arial", 13))
        self.hamburger_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.hamburger_btn.clicked.connect(self._toggle_nav_panel)
        left_layout.addWidget(self.hamburger_btn)
        
        self.warn_btn = QPushButton("¡")
        self.warn_btn.setToolTip("הערת שימוש")
        self.warn_btn.setFixedSize(30, 30)
        self.warn_btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.warn_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.warn_btn.clicked.connect(self._show_copyright_notice)
        left_layout.addWidget(self.warn_btn)

        # כפתור הגדרות
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setToolTip("הגדרות תצוגה")
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setFont(QFont("Arial", 15))
        self.settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.settings_btn.clicked.connect(self._open_settings)
        left_layout.addWidget(self.settings_btn)

        self.mode_btn = QPushButton("\U0001f520 תצוגת מילים")
        self.mode_btn.setFont(QFont("David", 11))
        self.mode_btn.setFixedHeight(30)
        self.mode_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.mode_btn.setCheckable(True)
        self.mode_btn.toggled.connect(self._on_mode_toggled)
        left_layout.addWidget(self.mode_btn)

        self.h_outer.addLayout(left_layout)

        # Center: Navigation and Title
        self.h_outer.addStretch(1)

        center_layout = QHBoxLayout()
        center_layout.setSpacing(20)

        self.prev_btn = QPushButton("→")
        self.prev_btn.setFixedSize(35, 35)
        self.prev_btn.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.prev_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.prev_btn.clicked.connect(self._go_prev_page)
        center_layout.addWidget(self.prev_btn)

        titles_widget = QWidget()
        titles_widget.setStyleSheet("background:transparent;")
        titles_vbox = QVBoxLayout(titles_widget)
        titles_vbox.setContentsMargins(0, 0, 0, 0)
        titles_vbox.setSpacing(2)

        self.page_title = QLabel("")
        self.page_title.setFont(QFont("David", 20, QFont.Weight.Bold))
        self.page_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titles_vbox.addWidget(self.page_title)

        self.page_sub = QLabel("")
        self.page_sub.setFont(QFont("Arial", 10))
        self.page_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titles_vbox.addWidget(self.page_sub)

        center_layout.addWidget(titles_widget)

        self.next_btn = QPushButton("←")
        self.next_btn.setFixedSize(35, 35)
        self.next_btn.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.next_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.next_btn.clicked.connect(self._go_next_page)
        center_layout.addWidget(self.next_btn)

        self.h_outer.addLayout(center_layout)
        self.h_outer.addStretch(1)

        # Right Side: Page Search Box
        self.page_search_box = QLineEdit()
        self.page_search_box.setPlaceholderText('חפש בדף...')
        self.page_search_box.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.page_search_box.setFont(QFont('David', 12))
        self.page_search_box.setFixedWidth(200)
        self.page_search_box.textChanged.connect(self._search_in_page)
        self.page_search_box.returnPressed.connect(self._search_in_page_next)
        self.h_outer.addWidget(self.page_search_box)

        self.ma_layout.addWidget(self.header)

        self.text_scroll = TouchScrollArea()
        self.text_scroll.setWidgetResizable(True)
        self.text_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.text_container = QWidget()
        self.text_container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.text_layout = QVBoxLayout(self.text_container)
        self.text_layout.setContentsMargins(12, 14, 12, 30)
        self.text_layout.setSpacing(8)
        self.text_layout.addStretch()

        self.text_scroll.setWidget(self.text_container)
        self.ma_layout.addWidget(self.text_scroll, 1)

        # Sidebar Panel
        self.page_panel = QWidget()
        pp_layout = QVBoxLayout(self.page_panel)
        pp_layout.setContentsMargins(0, 0, 0, 0)
        pp_layout.setSpacing(0)

        self.pg_hdr = QLabel("דפים")
        self.pg_hdr.setFont(QFont("Arial", 10))
        self.pg_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pp_layout.addWidget(self.pg_hdr)

        self.page_list = QListWidget()
        self.page_list.setObjectName("page_list")
        self.page_list.setFont(QFont("David", 14))
        self.page_list.setFixedWidth(85)
        self.page_list.currentRowChanged.connect(self._load_page)
        pp_layout.addWidget(self.page_list, 1)

        self.masechet_panel = QWidget()
        mp_layout = QVBoxLayout(self.masechet_panel)
        mp_layout.setContentsMargins(0, 0, 0, 0)
        mp_layout.setSpacing(0)

        self.ms_hdr = QLabel("מסכתות")
        self.ms_hdr.setFont(QFont("Arial", 10))
        self.ms_hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mp_layout.addWidget(self.ms_hdr)

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

        self.nav_panel = QWidget()
        nav_layout = QVBoxLayout(self.nav_panel)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText('חפש מסכת ודף...')
        self.search_box.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.search_box.setFont(QFont('David', 11))
        self.search_box.returnPressed.connect(self._quick_nav)
        nav_layout.addWidget(self.search_box)

        lists_row = QWidget()
        lists_row.setStyleSheet("background:transparent;")
        lists_h = QHBoxLayout(lists_row)
        lists_h.setContentsMargins(0, 0, 0, 0)
        lists_h.setSpacing(0)
        lists_h.addWidget(self.masechet_panel)
        lists_h.addWidget(self.page_panel)
        nav_layout.addWidget(lists_row, 1)

        self.splitter.addWidget(self.nav_panel)
        self.splitter.addWidget(self.main_area)
        self.splitter.addWidget(self.witness_panel)
        
        self.splitter.setSizes([215, 780, 420])
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)
        
        self._update_ui_colors()

    def _update_ui_colors(self):
        cfg = get_theme_config(self._theme)
        
        self.main_area.setStyleSheet(f"background-color:{cfg['main_bg']};")
        self.header.setStyleSheet(f"background-color:{cfg['header_bg']}; border-bottom: 1px solid {cfg['panel_header_border']};")
        self.page_title.setStyleSheet(f"color:{cfg['header_text']};background:transparent;")
        self.page_sub.setStyleSheet(f"color:{cfg['header_subtext']};background:transparent;")
        
        btn_style = f"""
            QPushButton {{
                color: {cfg['btn_color']};
                background: transparent;
                border: 2px solid {cfg['btn_color']};
                border-radius: 15px;
                padding-bottom: 2px;
            }}
            QPushButton:hover {{
                color: {cfg['btn_text_hover']};
                border-color: {cfg['btn_text_hover']};
                background: rgba(200,160,60,0.15);
            }}
        """
        self.warn_btn.setStyleSheet(btn_style)
        self.hamburger_btn.setStyleSheet(btn_style)

        self.settings_btn.setStyleSheet(f"""
            QPushButton {{ color: {cfg['btn_color']}; background: transparent; border: none; padding-bottom: 1px; }}
            QPushButton:hover {{ color: {cfg['btn_text_hover']}; }}
        """)
        
        self.mode_btn.setStyleSheet(f"""
            QPushButton {{
                color: {cfg['header_subtext'] if self._theme == 'colorful' else '#4A5568'};
                background: {cfg['search_bg'] if self._theme == 'colorful' else '#DDE4E9'};
                border: 1px solid {cfg['btn_border']};
                border-radius: 6px;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background: {cfg['btn_hover_bg'] if self._theme == 'colorful' else '#D1D9E0'};
                border-color: {cfg['btn_color'] if self._theme == 'colorful' else '#A0B4CC'};
            }}
            QPushButton:checked {{
                background: {cfg['section_selected_bg'] if self._theme == 'classic' else '#7A3810'};
                border-color: {cfg['section_selected_border'] if self._theme == 'classic' else '#E8C080'};
                color: {cfg['section_selected_right'] if self._theme == 'classic' else '#FFE8A0'};
            }}
        """)
        
        nav_btn_style = f"""
            QPushButton {{ color: {cfg['btn_color']}; background: transparent; border: 1px solid {cfg['btn_border']}; border-radius: 17px; }}
            QPushButton:hover {{ background: {cfg['btn_hover_bg']}; border-color: {cfg['btn_color']}; color: {cfg['header_text']}; }}
            QPushButton:disabled {{ color: {cfg['btn_border'] if self._theme == 'colorful' else '#CBD5E0'}; border-color: {cfg['btn_hover_bg'] if self._theme == 'colorful' else '#E1E8ED'}; }}
        """
        self.prev_btn.setStyleSheet(nav_btn_style)
        self.next_btn.setStyleSheet(nav_btn_style)
        
        self.page_search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: {cfg['search_bg']};
                color: {cfg['search_text']};
                border: 1px solid {cfg['search_border']};
                border-radius: 6px;
                padding: 5px 10px;
                selection-background-color: {cfg['btn_color']};
            }}
            QLineEdit:focus {{
                border: 1px solid {cfg['btn_color']};
                background-color: {cfg['search_bg'] if self._theme == 'classic' else '#4A2E1A'};
            }}
            QLineEdit::placeholder {{
                color: {cfg['search_placeholder']};
            }}
        """)
        
        self.text_scroll.setStyleSheet(f"QScrollArea{{border:none;background:{cfg['main_bg']};}}")
        self.text_container.setStyleSheet(f"background-color:{cfg['main_bg']};")
        
        self.nav_panel.setStyleSheet(f"background-color:{cfg['header_bg'] if self._theme == 'colorful' else '#D9E1E8'};")
        self.page_panel.setStyleSheet(f"background-color:{cfg['header_bg'] if self._theme == 'colorful' else '#E1E8ED'}; border-left: 1px solid {cfg['search_border']};")
        self.masechet_panel.setStyleSheet(f"background-color:{'#1A2B1A' if self._theme == 'colorful' else '#D9E1E8'}; border-left: 1px solid {cfg['search_border']};")
        
        self.pg_hdr.setStyleSheet(f"color:{cfg['btn_color']};padding:10px 6px 8px 6px;letter-spacing:2px;border-bottom:1px solid {cfg['btn_border']};")
        self.ms_hdr.setStyleSheet(f"color:{'#A8C060' if self._theme == 'colorful' else '#718096'};padding:10px 6px 8px 6px;letter-spacing:2px;border-bottom:1px solid {cfg['btn_border']};")

        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: {cfg['search_bg']};
                color: {cfg['search_text']};
                border: none;
                border-bottom: 1px solid {cfg['search_border']};
                padding: 7px 10px;
            }}
            QLineEdit:focus {{
                background-color: {cfg['search_bg'] if self._theme == 'classic' else '#4A2E1A'};
                border-bottom: 2px solid {cfg['btn_color']};
            }}
            QLineEdit::placeholder {{
                color: {cfg['search_placeholder']};
            }}
        """)

    def _toggle_nav_panel(self):
        if self.nav_panel.isVisible():
            self.nav_panel.hide()
            self.hamburger_btn.setText("◀")
        else:
            self.nav_panel.show()
            self.hamburger_btn.setText("▶")
            
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
        self.next_btn.setEnabled(idx < len(self.pages) - 1)

    def _quick_nav(self):
        text = self.search_box.text().strip()
        if not text: return
        m = re.match(r'^(.+?)\s+(.+)$', text)
        if m:
            q_ms, q_pg = m.groups()
        else:
            q_ms, q_pg = text, ''

        for i in range(self.masechet_list.count()):
            if _masechet_matches(self.masechtot[i]['name'], q_ms):
                self.masechet_list.setCurrentRow(i)
                if q_pg:
                    for j in range(self.page_list.count()):
                        if _page_matches(self.pages[j]['page'], q_pg):
                            self.page_list.setCurrentRow(j)
                            break
                return

    def _search_in_page(self, text: str):
        self._page_search_term = text.strip()
        self._page_search_idx = -1
        
        if self.display_mode == 'words' and self._words_view:
            self._words_view.search_highlight(self._page_search_term)
            matching = self._words_view.get_match_widgets()
        else:
            for block in self.section_blocks:
                block.search_highlight(self._page_search_term)
            matching = [b for b in self.section_blocks if b.has_search_match()]

        cfg = get_theme_config(self._theme)
        if matching:
            self.page_search_box.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {cfg['search_bg']};
                    color: {cfg['search_text']};
                    border: 1px solid {cfg['btn_color']};
                    border-radius: 6px;
                    padding: 5px 10px;
                }}
                QLineEdit:focus {{
                    border: 1px solid {cfg['btn_color']};
                    background-color: {cfg['search_bg'] if self._theme == 'classic' else '#4A2E1A'};
                }}
            """)
            self._page_search_idx = 0
            self._scroll_to_search_result(0)
        else:
            self.page_search_box.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {cfg['search_bg'] if self._theme == 'classic' else '#F0F4F7'};
                    color: {cfg['search_text']};
                    border: 1px solid #CC3300;
                    border-radius: 6px;
                    padding: 5px 10px;
                }}
                QLineEdit:focus {{
                    border: 1px solid #CC3300;
                    background-color: {cfg['search_bg'] if self._theme == 'classic' else '#4A2E1A'};
                }}
            """)

    def _search_in_page_next(self):
        if not hasattr(self, '_page_search_term') or not self._page_search_term:
            return

        if self.display_mode == 'words' and self._words_view:
            matching = self._words_view.get_match_widgets()
        else:
            matching = [b for b in self.section_blocks if b.has_search_match()]

        if not matching:
            return
        self._page_search_idx = (self._page_search_idx + 1) % len(matching)
        self._scroll_to_search_result(self._page_search_idx)

    def _scroll_to_search_result(self, result_idx: int):
        if self.display_mode == 'words' and self._words_view:
            matching = self._words_view.get_match_widgets()
        else:
            matching = [b for b in self.section_blocks if b.has_search_match()]

        if 0 <= result_idx < len(matching):
            widget = matching[result_idx]
            self.text_scroll.ensureWidgetVisible(widget)

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
        self._page_search_term = ''
        self._page_search_idx = -1
        self.page_search_box.clear()
        
        cfg = get_theme_config(self._theme)
        self.page_search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: {cfg['search_bg']};
                color: {cfg['search_text']};
                border: 1px solid {cfg['search_border']};
                border-radius: 6px;
                padding: 5px 10px;
                selection-background-color: {cfg['btn_color']};
            }}
            QLineEdit:focus {{
                border: 1px solid {cfg['btn_color']};
                background-color: {cfg['search_bg'] if self._theme == 'classic' else '#4A2E1A'};
            }}
        """)
        
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
            block = SectionBlock(section, self.main_witness,
                                 font_family=self._font_family,
                                 font_size=self._font_size,
                                 theme=self._theme)
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
            lbl.setStyleSheet(f"color:{get_theme_config(self._theme)['word_missing_text']};font-size:14px;padding:40px;")
            self.text_layout.insertWidget(self.text_layout.count() - 1, lbl)
            return

        wv = WordsView(words_data, self.main_witness,
                       font_family=self._font_family,
                       font_size=self._font_size,
                       theme=self._theme)
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
        if self.display_mode == 'words' and self._current_words_data:
            key = event.key()
            if key == Qt.Key.Key_Left:
                if self._current_word_idx < 0:
                    new_idx = 0
                else:
                    new_idx = self._current_word_idx + 1
            elif key == Qt.Key.Key_Right:
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