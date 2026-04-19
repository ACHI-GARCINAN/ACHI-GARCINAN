from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont, QCursor

from styles import get_theme_config


class _ClickableWord(QLabel):
    """מילה לחיצה בודדת בתצוגת המילים."""
    clicked = pyqtSignal(int)

    def __init__(self, text: str, idx: int, is_present: bool,
                 font_family: str = 'David', font_size: int = 16, theme: str = 'classic', parent=None):
        super().__init__(text, parent)
        self.idx = idx
        self.is_present = is_present
        self.is_selected = False
        self.is_search_match = False
        self._theme = theme
        self.setFont(QFont(font_family, font_size))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._apply_style()

    def _apply_style(self):
        cfg = get_theme_config(self._theme)
        if self.is_selected:
            style = f"background:{cfg['word_selected_bg']};color:{cfg['word_selected_text']};padding:1px 2px;border-radius:3px;font-weight:bold;"
        elif self.is_search_match:
            style = "background:#FFD700;color:#1A202C;padding:1px 2px;border-radius:3px;"
        elif not self.is_present:
            style = f"background:transparent;color:{cfg['word_missing_text']};padding:1px 2px;border-radius:3px;font-style:italic;"
        else:
            style = f"background:transparent;color:{cfg['word_normal_text']};padding:1px 2px;border-radius:3px;"
        self.setStyleSheet(style)

    def set_selected(self, val: bool):
        self.is_selected = val
        self._apply_style()

    def set_search_match(self, val: bool):
        self.is_search_match = val
        self._apply_style()

    def update_font(self, font_family: str, font_size: int, theme: str = None):
        if theme:
            self._theme = theme
        self.setFont(QFont(font_family, font_size))
        self._apply_style()

    def enterEvent(self, e):
        if not self.is_selected:
            cfg = get_theme_config(self._theme)
            self.setStyleSheet(f"background:{cfg['word_hover_bg']};color:{cfg['word_hover_text']};padding:1px 2px;border-radius:3px;")
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._apply_style()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.idx)
            top = self.window()
            if top:
                top.setFocus()
        super().mousePressEvent(e)


class _FlowWidget(QWidget):
    """Flow layout — מציג מילים בשורות גמישות RTL."""
    word_clicked = pyqtSignal(int)

    def __init__(self, words_data: list, main_witness: str,
                 font_family: str = 'David', font_size: int = 16, theme: str = 'classic', parent=None):
        super().__init__(parent)
        self.words_data = words_data
        self.main_witness = main_witness
        self._labels: list[_ClickableWord] = []
        self._selected_idx = -1
        self._h_spacing = 1
        self._v_spacing = 7
        self._font_family = font_family
        self._font_size = font_size
        self._theme = theme

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        for i, wd in enumerate(words_data):
            text = wd['witnesses'].get(main_witness)
            if text == 'None':
                text = None
            display = text if text else '—'
            lbl = _ClickableWord(display, i, text is not None, font_family, font_size, theme, self)
            lbl.clicked.connect(self._on_word_clicked)
            self._labels.append(lbl)

        self.setMinimumHeight(60)

    def _on_word_clicked(self, idx: int):
        self.select_word(idx)
        self.word_clicked.emit(idx)

    def select_word(self, idx: int):
        if 0 <= self._selected_idx < len(self._labels):
            self._labels[self._selected_idx].set_selected(False)
        self._selected_idx = idx
        if 0 <= idx < len(self._labels):
            self._labels[idx].set_selected(True)

    def update_font(self, font_family: str, font_size: int, theme: str = None):
        self._font_family = font_family
        self._font_size = font_size
        if theme:
            self._theme = theme
        for lbl in self._labels:
            lbl.update_font(font_family, font_size, theme)
            lbl.adjustSize()
        self._do_layout(self.width())
        QTimer.singleShot(0, lambda: self._do_layout(self.width()))
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._do_layout(self.width())

    def showEvent(self, event):
        super().showEvent(event)
        self._do_layout(self.width())

    def _do_layout(self, width: int):
        if width <= 0:
            return
        margin = 8
        usable = width - 2 * margin

        for lbl in self._labels:
            lbl.adjustSize()

        rows: list[list] = []
        current_row: list = []
        current_w = 0
        min_spacing = self._h_spacing

        for lbl in self._labels:
            w = lbl.sizeHint().width() + 2
            needed = w if not current_row else w + min_spacing
            if current_row and current_w + needed > usable:
                rows.append(current_row)
                current_row = [lbl]
                current_w = w
            else:
                current_row.append(lbl)
                current_w += needed

        if current_row:
            rows.append(current_row)

        y = 4
        for r_idx, row in enumerate(rows):
            row_h = max(lbl.sizeHint().height() for lbl in row)
            total_word_w = sum(lbl.sizeHint().width() + 2 for lbl in row)

            is_last_row = (r_idx == len(rows) - 1)
            if len(row) > 1 and not is_last_row:
                gap = (usable - total_word_w) / (len(row) - 1)
            else:
                gap = min_spacing

            x = width - margin
            for lbl in row:
                w = lbl.sizeHint().width() + 2
                h = lbl.sizeHint().height()
                lbl.setGeometry(int(x - w), y, w, h)
                x -= w + gap

            y += row_h + self._v_spacing

        total_h = y + 8
        self.setMinimumHeight(total_h)
        self.updateGeometry()

    def sizeHint(self):
        return QSize(self.width(), self.minimumHeight())

    def search_highlight(self, term: str) -> bool:
        if not term:
            for lbl in self._labels:
                lbl.set_search_match(False)
            return False
        found = False
        import re
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        for lbl in self._labels:
            if pattern.search(lbl.text()):
                lbl.set_search_match(True)
                found = True
            else:
                lbl.set_search_match(False)
        return found

    def get_match_widgets(self) -> list:
        return [lbl for lbl in self._labels if lbl.is_search_match]


class WordsView(QWidget):
    """
    מציג את כל המילים של דף ברצף.
    לחיצה על מילה מציגה את עדי הנוסח בפאנל הצדדי.
    """
    word_clicked = pyqtSignal(int)

    def __init__(self, words_data: list, main_witness: str,
                 font_family: str = 'David', font_size: int = 16, theme: str = 'classic', parent=None):
        super().__init__(parent)
        self.words_data = words_data
        self.main_witness = main_witness
        self.selected_idx = -1
        self._theme = theme

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._update_ui_colors()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 14, 18, 20)
        outer.setSpacing(0)

        self._flow_widget = _FlowWidget(words_data, main_witness, font_family, font_size, theme)
        self._flow_widget.word_clicked.connect(self.word_clicked.emit)
        outer.addWidget(self._flow_widget)
        outer.addStretch()

    def _update_ui_colors(self):
        cfg = get_theme_config(self._theme)
        self.setStyleSheet(f"background-color:{cfg['main_bg']};")

    def select_word(self, idx: int):
        self._flow_widget.select_word(idx)
        self.selected_idx = idx

    def clear_selection(self):
        self._flow_widget.select_word(-1)
        self.selected_idx = -1

    def update_font(self, font_family: str, font_size: int, theme: str = None):
        if theme:
            self._theme = theme
            self._update_ui_colors()
        self._flow_widget.update_font(font_family, font_size, theme)

    def search_highlight(self, term: str) -> bool:
        return self._flow_widget.search_highlight(term)

    def get_match_widgets(self) -> list:
        return self._flow_widget.get_match_widgets()
