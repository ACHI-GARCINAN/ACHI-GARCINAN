import re
import sys
import os
import ctypes
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QSplitter,
    QPushButton, QLineEdit, QSpacerItem, QSizePolicy
)
from widgets.witness_panel import WitnessPanel
from widgets.touch_scroll import TouchScrollArea
from PyQt6.QtCore import Qt, QObject, QEvent

from PyQt6.QtGui import QFont, QCursor, QIcon, QKeyEvent
from styles import get_theme_styles, get_theme_config
from db import fetch_masechet, fetch_page, fetch_page_words
from utils import _page_matches, _masechet_matches
from settings_manager import load_settings, save_settings, save_last_position, load_last_position, save_layout, load_layout
from icons import get_theme_icon, IconName


def get_base_dir() -> str:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def get_icon() -> QIcon:
    base = get_base_dir()
    for name in ('logo.ico', 'logo.png', 'icon.ico', 'icon.png'):
        path = os.path.join(base, name)
        if os.path.exists(path):
            return QIcon(path)
    return QIcon()





class _ListArrowFilter(QObject):
    """מונע מ-QListWidget לבלוע חצי מקלדת בתצוגת מילים — מעביר אותם ל-MainWindow."""

    def __init__(self, window):
        super().__init__()
        self._window = window

    def eventFilter(self, obj, event):
        if (event.type() == QEvent.Type.KeyPress
                and self._window.display_mode == 'words'):
            key = event.key()
            if key in (Qt.Key.Key_Left, Qt.Key.Key_Right,
                       Qt.Key.Key_Up, Qt.Key.Key_Down):
                self._window.keyPressEvent(event)
                return True
        return False


class ListTouchScrollFilter(QObject):
    """מאפשר גלילה במסך מגע ב-QListWidget."""

    def __init__(self):
        super().__init__()
        self._touch_start = None
        self._scroll_start = None

    def eventFilter(self, obj, event):
        t = event.type()
        if t == QEvent.Type.TouchBegin:
            pts = event.points()
            if pts:
                self._touch_start = pts[0].position().toPoint()
                sb = obj.parent().verticalScrollBar()
                self._scroll_start = sb.value()
            return True
        if t == QEvent.Type.TouchUpdate:
            pts = event.points()
            if pts and self._touch_start is not None:
                delta = pts[0].position().toPoint().y() - self._touch_start.y()
                sb = obj.parent().verticalScrollBar()
                sb.setValue(self._scroll_start - delta)
            return True
        if t == QEvent.Type.TouchEnd:
            self._touch_start = None
            return True
        return False


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
        self._continuous_sections_view = settings.get('continuous_sections_view', False)

        self.setWindowTitle("נוסחאות התלמוד")
        self.setMinimumSize(1100, 650)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # החל עיצוב לפי ערכת הנושא
        style_str, _ = get_theme_styles(self._theme)
        self.setStyleSheet(style_str)
        
        self.setWindowIcon(get_icon())
        
        self.display_mode = 'sections'
        self._words_view = None

        self._build_ui()                        # ← קודם בונים
        # שחזר פריסה שמורה
        _layout = load_layout()
        self.splitter.setSizes(_layout['splitter_sizes'])
        if not _layout['sidebar_visible']:
            self.nav_panel.hide()
            self.sidebar_toggle_btn.setIcon(get_theme_icon(IconName.SIDEBAR_SHOW, self._theme, 18))

        # גלילת מסך מגע עבור רשימות המסכתות והדפים
        self._list_touch_filter = ListTouchScrollFilter()
        self._list_arrow_filter = _ListArrowFilter(self)
        for lw in (self.masechet_list, self.page_list):
            lw.viewport().setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
            lw.viewport().installEventFilter(self._list_touch_filter)
            lw.installEventFilter(self._list_arrow_filter)

        if self.masechtot:
            last_ms, last_pg = load_last_position()
            last_ms = min(last_ms, len(self.masechtot) - 1)
            self._restore_page_idx = last_pg
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(150, lambda: self.masechet_list.setCurrentRow(last_ms))            
    def _show_copyright_notice(self):
        from widgets.copyright_popup import CopyrightPopup
        popup = CopyrightPopup(self.centralWidget())
        popup.exec()

    def _open_settings(self):
        from widgets.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self._font_family, self._font_size, self._theme, self._continuous_sections_view, self)
        dlg.settings_changed.connect(self._apply_settings)
        dlg.exec()

    def _apply_settings(self, font_family: str, font_size: int, theme: str, continuous_sections_view: bool = False):
        # Validate inputs
        if not isinstance(font_size, int) or font_size < 8 or font_size > 48:
            print(f"Warning: Invalid font_size {font_size}, using default 16")
            font_size = 16
        if not isinstance(font_family, str) or not font_family.strip():
            print(f"Warning: Invalid font_family {font_family}, using default 'David'")
            font_family = 'David'
        if theme not in ('classic', 'colorful'):
            print(f"Warning: Invalid theme {theme}, using default 'classic'")
            theme = 'classic'
        
        self._font_family = font_family
        self._font_size = font_size
        theme_changed = (self._theme != theme)
        continuous_changed = (self._continuous_sections_view != continuous_sections_view)
        self._theme = theme
        self._continuous_sections_view = continuous_sections_view
        
        # שמור להגדרות
        save_settings({
            'font_family': font_family, 
            'font_size': font_size,
            'theme': theme,
            'continuous_sections_view': continuous_sections_view,
        })
        
        # עדכן עיצוב אם ערכת הנושא השתנתה
        if theme_changed:
            style_str, _ = get_theme_styles(theme)
            self.setStyleSheet(style_str)
            self._update_ui_colors()
            self.style().unpolish(self)
            self.style().polish(self)
            # רענון הדף הנוכחי כדי להחיל צבעים חדשים
            if self.pages:
                self._load_page(self.current_page_idx)
        elif continuous_changed and self.pages:
            # רענון הדף הנוכחי כדי להחיל שינוי תצוגה רציפה
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

        self.warn_btn = QPushButton()
        self.warn_btn.setIcon(get_theme_icon(IconName.INFO, self._theme, 18))  # הוספת האייקון
        self.warn_btn.setToolTip("הערת שימוש")
        self.warn_btn.setFixedSize(30, 30)
        self.warn_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.warn_btn.clicked.connect(self._show_copyright_notice)
        left_layout.addWidget(self.warn_btn)
        
        # כפתור הגדרות
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(get_theme_icon(IconName.SETTINGS, self._theme, 18))  # הוספת האייקון החדש
        self.settings_btn.setToolTip("הגדרות תצוגה")
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.settings_btn.clicked.connect(self._open_settings)
        left_layout.addWidget(self.settings_btn)
 
        self.mode_btn = QPushButton()
        self.mode_btn.setIcon(get_theme_icon(IconName.MODE_WORDS, self._theme, 16))
        self.mode_btn.setText("תצוגת מילים")
        self.mode_btn.setFont(QFont("David", 11))
        self.mode_btn.setFixedHeight(30)
        self.mode_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.mode_btn.setCheckable(True)
        self.mode_btn.setToolTip("עבור בין תצוגת מילים לתצוגת קטעים (Alt+M)")
        self.mode_btn.toggled.connect(self._on_mode_toggled)
        left_layout.addWidget(self.mode_btn)

        self.h_outer.addLayout(left_layout)

        # כפתור הצגת/הסתרת סרגל צד — חץ מתחלף
        self.sidebar_toggle_btn = QPushButton()
        self.sidebar_toggle_btn.setIcon(get_theme_icon(IconName.SIDEBAR_HIDE, self._theme, 18))  # הוספת האייקון החדש
        self.sidebar_toggle_btn.setToolTip("הצג/הסתר סרגל מסכתות")
        self.sidebar_toggle_btn.setFixedSize(30, 30)
        self.sidebar_toggle_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.sidebar_toggle_btn.clicked.connect(self._toggle_sidebar)
        self.h_outer.insertWidget(0, self.sidebar_toggle_btn)
        # Center: Navigation and Title
        self.h_outer.addStretch(1)

        center_layout = QHBoxLayout()
        center_layout.setSpacing(20)

        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(get_theme_icon(IconName.NAV_PREV, self._theme, 20))
        self.prev_btn.setFont(QFont())  # ניקוי גופן ישן
        self.prev_btn.setFixedSize(35, 35)
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

        self.next_btn = QPushButton()
        self.next_btn.setIcon(get_theme_icon(IconName.NAV_NEXT, self._theme, 20))
        self.next_btn.setFixedSize(35, 35)
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

        # שורת קרדיט בתחתית
        self.credit_bar = QWidget()
        self.credit_bar.setFixedHeight(22)
        credit_layout = QHBoxLayout(self.credit_bar)
        credit_layout.setContentsMargins(8, 0, 8, 0)
        credit_layout.setSpacing(0)
        self.credit_label = QLabel(
            "באדיבות הספרייה הלאומית לישראל, ואגודת פרידברג לכתבי יד יהודיים  |  כל הזכויות שמורות"
        )
        self.credit_label.setFont(QFont("David", 8))
        self.credit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credit_layout.addWidget(self.credit_label)
        self.ma_layout.addWidget(self.credit_bar)

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
        self.masechet_list.setFixedWidth(148)
        self.masechet_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

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
        self.splitter.splitterMoved.connect(self._on_splitter_moved)
        
        self._update_ui_colors()

    def _update_ui_colors(self):
        if getattr(self, '_last_applied_theme', None) == self._theme:
            return
        self._last_applied_theme = self._theme
        cfg = get_theme_config(self._theme)
        
        self.main_area.setStyleSheet(f"background-color:{cfg['main_bg']};")
        self.header.setStyleSheet(f"background-color:{cfg['header_bg']}; border-bottom: 1px solid {cfg['panel_header_border']};")
        self.page_title.setStyleSheet(f"color:{cfg['header_text']};background:transparent;")
        self.page_sub.setStyleSheet(f"color:{cfg['header_subtext']};background:transparent;")
        
        self.warn_btn.setIcon(get_theme_icon(IconName.INFO, self._theme, 18))
        self.settings_btn.setIcon(get_theme_icon(IconName.SETTINGS, self._theme, 18))
        is_visible = self.nav_panel.isVisible() if hasattr(self, 'nav_panel') else True
        _sb_icon = IconName.SIDEBAR_HIDE if is_visible else IconName.SIDEBAR_SHOW
        self.sidebar_toggle_btn.setIcon(get_theme_icon(_sb_icon, self._theme, 18))
        self.prev_btn.setIcon(get_theme_icon(IconName.NAV_PREV, self._theme, 20))
        self.next_btn.setIcon(get_theme_icon(IconName.NAV_NEXT, self._theme, 20))
        _mode_icon = IconName.MODE_SECTIONS if self.display_mode == 'words' else IconName.MODE_WORDS
        self.mode_btn.setIcon(get_theme_icon(_mode_icon, self._theme, 16))

        
        icon_btn_style = f"""
            QPushButton {{
                color: {cfg['btn_color']};
                background: transparent;
                border: 2px solid {cfg['btn_color']};
                border-radius: 13px;
                padding-bottom: 1px;
            }}
            QPushButton:hover {{
                color: {cfg['btn_text_hover']};
                border-color: {cfg['btn_text_hover']};
                background: rgba(200,160,60,0.15);
            }}
        """
        self.warn_btn.setStyleSheet(icon_btn_style)
        self.settings_btn.setStyleSheet(icon_btn_style)
        self.sidebar_toggle_btn.setStyleSheet(icon_btn_style)
        
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

        # עיצוב שורת הקרדיט לפי ערכת נושא
        if hasattr(self, 'credit_bar'):
            self.credit_bar.setStyleSheet(
                f"background-color:{cfg['header_bg']}; border-top: 1px solid {cfg['panel_header_border']};"
            )
            self.credit_label.setStyleSheet(
                f"color:{cfg['header_subtext']}; background:transparent;"
            )

    def _go_prev_page(self):
        row = self.page_list.currentRow()
        if row > 0:
            self.page_list.setCurrentRow(row - 1)
        if self.display_mode == 'words':
            self.setFocus()

    def _go_next_page(self):
        row = self.page_list.currentRow()
        if row < self.page_list.count() - 1:
            self.page_list.setCurrentRow(row + 1)
        if self.display_mode == 'words':
            self.setFocus()

    def _update_nav_buttons(self, idx: int):
        self.prev_btn.setEnabled(idx > 0)
        self.next_btn.setEnabled(idx < len(self.pages) - 1)

    def _toggle_sidebar(self):
        if self.nav_panel.isVisible():
            self.nav_panel.hide()
            self.sidebar_toggle_btn.setIcon(get_theme_icon(IconName.SIDEBAR_SHOW, self._theme, 18))  # ← מראה "לחץ להציג"
            self.splitter.setSizes([0, 995, 420])
        else:
            self.nav_panel.show()
            self.sidebar_toggle_btn.setIcon(get_theme_icon(IconName.SIDEBAR_HIDE, self._theme, 18))  # ← מראה "לחץ להסתיר"
            self.splitter.setSizes([215, 780, 420])
            save_layout(self.splitter.sizes(), self.nav_panel.isVisible())
            self.splitter.setSizes([215, 780, 420])
        save_layout(self.splitter.sizes(), self.nav_panel.isVisible())
    def _quick_nav(self):
        raw = self.search_box.text().strip()
        if not raw:
            return

        # ניתוח הקלט: מחלצים שם מסכת ומספר דף
        # תומך בראשי תיבות ובפורמטים גמישים
        acronyms = {
            'ר"ה': 'ראש השנה',
            'מו"ק': 'מועד קטן',
            'ב"ק': 'בבא קמא',
            'ב"מ': 'בבא מציעא',
            'ב"ב': 'בבא בתרא',
            'ע"ז': 'עבודה זרה'
        }

        ms_query = ""
        pg_query = ""

        # בדוק אם השאילתה מתחילה בראשי תיבות
        found_acronym = False
        for abbr, full in acronyms.items():
            if raw == abbr or raw.startswith(abbr + " "):
                ms_query = full
                pg_query = raw[len(abbr):].strip()
                # נקה את המילה "דף" אם קיימת
                pg_query = re.sub(r'^\u05d3\u05e3\s*', '', pg_query).strip()
                found_acronym = True
                break

        if not found_acronym:
            # תבנית רגילה: <מסכת> [דף] <מספר>
            m = re.match(
                r'^([\u05d0-\u05ea]+(?:\s[\u05d0-\u05ea]+)*)'
                r'(?:\s+\u05d3\u05e3)?'
                r'\s+([\u05d0-\u05ea"\u05f4\u05f3\u2019\']+|\d+)$',
                raw
            )
            if m:
                ms_query = m.group(1).strip()
                pg_query = m.group(2).strip()
            else:
                # אם אין מספר דף, נסה לראות אם זה רק שם מסכת
                ms_query = raw
                pg_query = ""

        if not ms_query:
            # לא הצלחנו לפרש — סמן שגיאה בתיבת החיפוש
            cfg = get_theme_config(self._theme)
            self.search_box.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {cfg['search_bg']};
                    color: {cfg['search_text']};
                    border: none;
                    border-bottom: 2px solid #CC3300;
                    padding: 7px 10px;
                }}
            """)
            return

        # מצא את המסכת
        ms_idx = None
        for i, ms in enumerate(self.masechtot):
            if _masechet_matches(ms['name'], ms_query):
                ms_idx = i
                break

        if ms_idx is None:
            cfg = get_theme_config(self._theme)
            self.search_box.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {cfg['search_bg']};
                    color: {cfg['search_text']};
                    border: none;
                    border-bottom: 2px solid #CC3300;
                    padding: 7px 10px;
                }}
            """)
            return

        # טען את המסכת אם צריך
        if self.masechet_list.currentRow() != ms_idx:
            self.masechet_list.setCurrentRow(ms_idx)

        # מצא את הדף
        pg_idx = None
        if not pg_query:
            # אם לא הוזן דף, נבחר את הדף הראשון במסכת
            pg_idx = 0
        else:
            for i, pg in enumerate(self.pages):
                if _page_matches(pg['page'], pg_query):
                    pg_idx = i
                    break

        if pg_idx is None:
            cfg = get_theme_config(self._theme)
            self.search_box.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {cfg['search_bg']};
                    color: {cfg['search_text']};
                    border: none;
                    border-bottom: 2px solid #CC3300;
                    padding: 7px 10px;
                }}
            """)
            return

        self.page_list.setCurrentRow(pg_idx)
        self.search_box.clear()
        self.search_box.clearFocus()
        if self.display_mode == 'words':
            self.setFocus()
        # החזר סגנון רגיל
        cfg = get_theme_config(self._theme)
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

    def _search_in_page(self, text: str):
        self._page_search_term = text.strip()
        self._page_search_idx = -1

        cfg = get_theme_config(self._theme)

        if self.display_mode == 'words' and self._words_view:
            self._words_view.search_highlight(self._page_search_term)
            matching = self._words_view.get_match_widgets()
        else:
            for block in self.section_blocks:
                block.search_highlight(self._page_search_term)
            matching = [b for b in self.section_blocks if b.has_search_match()]

        if not self._page_search_term:
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
            return

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
            # שחזר דף אחרון אם יש (בטעינה ראשונה)
            restore_idx = getattr(self, '_restore_page_idx', 0)
            self._restore_page_idx = 0  # אפס כדי שמעכשיו תמיד יתחיל מדף ראשון בעת החלפת מסכת
            restore_idx = min(restore_idx, len(pages) - 1)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.page_list.setCurrentRow(restore_idx))
            
    def _load_page(self, idx: int):
        if idx < 0 or idx >= len(self.pages):
            return
        self.current_page_idx = idx
        # שמור מיקום נוכחי — debounce: רק אחרי 2 שניות של שקט
        # בטל טיימר קודם לעיתים אם עדיין פעיל (מניעת race condition)
        if hasattr(self, '_save_pos_timer') and self._save_pos_timer.isActive():
            self._save_pos_timer.stop()
        
        if not hasattr(self, '_save_pos_timer'):
            from PyQt6.QtCore import QTimer
            self._save_pos_timer = QTimer()
            self._save_pos_timer.setSingleShot(True)
            self._save_pos_timer.timeout.connect(
                lambda: save_last_position(self.masechet_list.currentRow(), self.current_page_idx)
            )
        self._save_pos_timer.start(2000)        # ← כותב לדיסק רק אחרי 2 שניות בלי שינוי
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

        if self.display_mode == 'words':
            self._load_page_words(page)         # ← בלי sections, בלי קריאת DB מיותרת
        else:
            sections = fetch_page(page['_id'])  # ← נקרא רק כשצריך
            self._load_page_sections(sections, page['page'])
            
        self.text_scroll.verticalScrollBar().setValue(0)
        self.witness_panel.reset()

    def _load_page_sections(self, sections: list, page_label: str):
        from widgets.section_block import SectionBlock
        if self._continuous_sections_view:
            self.text_layout.setSpacing(0)
            self.text_layout.setContentsMargins(12, 14, 12, 30)
        else:
            self.text_layout.setSpacing(8)
            self.text_layout.setContentsMargins(12, 14, 12, 30)

        for section in sections:
            block = SectionBlock(section, self.main_witness,
                                 font_family=self._font_family,
                                 font_size=self._font_size,
                                 theme=self._theme,
                                 continuous_view=self._continuous_sections_view)
            block.clicked.connect(
                lambda checked=False, s=section, b=block, p=page_label:
                    self._select_section(s, b, p)
            )
            self.text_layout.insertWidget(self.text_layout.count() - 1, block)
            self.section_blocks.append(block)

    def _load_page_words(self, page: dict):
        from widgets.words_view import WordsView
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
        prev_section_label = ''
        if self.selected_block:
            prev_section_label = self.selected_block.section.get('section', '')
        elif self._current_words_data and self._current_word_idx >= 0:
            wd = self._current_words_data[self._current_word_idx]
            prev_section_label = wd.get('section', '')

        if checked:
            self.display_mode = 'words'
            self.mode_btn.setText("תצוגת קטעים")
            self.mode_btn.setIcon(get_theme_icon(IconName.MODE_SECTIONS, self._theme, 16))
        else:
            self.display_mode = 'sections'
            self.mode_btn.setText("תצוגת מילים")
            self.mode_btn.setIcon(get_theme_icon(IconName.MODE_WORDS, self._theme, 16))

        if not self.pages:
            return

        self._load_page(self.current_page_idx)

        if not prev_section_label:
            if self.display_mode == 'words':
                self.setFocus()
            return

        page = self.pages[self.current_page_idx]['page']

        if self.display_mode == 'words' and self._current_words_data:
            for i, wd in enumerate(self._current_words_data):
                if wd.get('section', '') == prev_section_label:
                    self._select_word(i, self._current_words_data, page)
                    if self._words_view and self._words_view._flow_widget:
                        lbl = self._words_view._flow_widget._labels[i]
                        from PyQt6.QtCore import QTimer
                        QTimer.singleShot(50, lambda w=lbl: self.text_scroll.ensureWidgetVisible(w))
                    self.setFocus()
                    break

        elif self.display_mode == 'sections' and self.section_blocks:
            for block in self.section_blocks:
                if block.section.get('section', '') == prev_section_label:
                    section = block.section
                    self._select_section(section, block, page)
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(50, lambda b=block: self.text_scroll.ensureWidgetVisible(b))
                    break
                    
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

    def _on_splitter_moved(self, pos: int, index: int):
        save_layout(self.splitter.sizes(), self.nav_panel.isVisible())

    def closeEvent(self, event):
        """שומר את המיקום האחרון בסגירת התוכנה."""
        ms_idx = self.masechet_list.currentRow()
        pg_idx = self.current_page_idx
        if ms_idx >= 0 and pg_idx >= 0:
            save_last_position(ms_idx, pg_idx)
        super().closeEvent(event)

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
            elif key == Qt.Key.Key_Down:
                if self._current_word_idx < 0 or not self._words_view:
                    new_idx = 0
                else:
                    adj = self._words_view.get_word_at_adjacent_row(self._current_word_idx, 1)
                    new_idx = adj if adj >= 0 else self._current_word_idx
            elif key == Qt.Key.Key_Up:
                if self._current_word_idx < 0 or not self._words_view:
                    new_idx = 0
                else:
                    adj = self._words_view.get_word_at_adjacent_row(self._current_word_idx, -1)
                    new_idx = adj if adj >= 0 else self._current_word_idx
            else:
                super().keyPressEvent(event)
                return
            new_idx = max(0, min(new_idx, len(self._current_words_data) - 1))
            if new_idx != self._current_word_idx:
                page = self.pages[self.current_page_idx]['page']
                self._select_word(new_idx, self._current_words_data, page)
                if self._words_view:
                    lbl = self._words_view._flow_widget._labels[new_idx]
                    self.text_scroll.ensureWidgetVisible(lbl)
            return
        super().keyPressEvent(event)
