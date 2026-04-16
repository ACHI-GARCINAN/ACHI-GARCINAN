from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QCursor


class _ClickableWord(QLabel):
    """מילה לחיצה בודדת בתצוגת המילים."""
    clicked = pyqtSignal(int)

    _NORMAL   = "background:transparent;color:#2D3748;padding:1px 1px;border-radius:3px;"
    _HOVER    = "background:#E1E8ED;color:#2D3748;padding:1px 1px;border-radius:3px;"
    _SELECTED = "background:#A0B4CC;color:#1A202C;padding:1px 1px;border-radius:3px;font-weight:bold;"
    _MISSING  = "background:transparent;color:#A0AEC0;padding:1px 1px;border-radius:3px;font-style:italic;"

    def __init__(self, text: str, idx: int, is_present: bool, parent=None):
        super().__init__(text, parent)
        self.idx = idx
        self.is_present = is_present
        self.is_selected = False
        self.setFont(QFont("David", 16))
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._apply_style()

    def _apply_style(self):
        if self.is_selected:
            self.setStyleSheet(self._SELECTED)
        elif not self.is_present:
            self.setStyleSheet(self._MISSING)
        else:
            self.setStyleSheet(self._NORMAL)

    def set_selected(self, val: bool):
        self.is_selected = val
        self._apply_style()

    def enterEvent(self, e):
        if not self.is_selected:
            self.setStyleSheet(self._HOVER)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._apply_style()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.idx)
            # Return focus to the main window so keyboard arrow events work
            top = self.window()
            if top:
                top.setFocus()
        super().mousePressEvent(e)


class _FlowWidget(QWidget):
    """
    ווידג'ט עם flow layout — מציג מילים בשורות גמישות (RTL).
    """
    word_clicked = pyqtSignal(int)

    def __init__(self, words_data: list, main_witness: str, parent=None):
        super().__init__(parent)
        self.words_data = words_data
        self.main_witness = main_witness
        self._labels: list[_ClickableWord] = []
        self._selected_idx = -1
        self._h_spacing = 1
        self._v_spacing = 7

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        for i, wd in enumerate(words_data):
            text = wd['witnesses'].get(main_witness)
            if text == 'None':
                text = None
            display = text if text else '—'
            lbl = _ClickableWord(display, i, text is not None, self)
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._do_layout(self.width())

    def showEvent(self, event):
        super().showEvent(event)
        self._do_layout(self.width())

    def _do_layout(self, width: int):
        if width <= 0:
            return
        # RTL: נסדר מימין לשמאל
        x = width
        y = 4
        row_height = 0
        margin = 8

        for lbl in self._labels:
            lbl.adjustSize()
            w = lbl.sizeHint().width() + 2
            h = lbl.sizeHint().height()

            if x - w < margin and x < width:
                # שורה חדשה
                x = width
                y += row_height + self._v_spacing
                row_height = 0

            x_pos = x - w
            lbl.setGeometry(x_pos, y, w, h)
            x -= w + self._h_spacing
            row_height = max(row_height, h)

        total_h = y + row_height + 8
        self.setMinimumHeight(total_h)
        self.updateGeometry()

    def sizeHint(self):
        return QSize(self.width(), self.minimumHeight())


class WordsView(QWidget):
    """
    מציג את כל המילים של דף ברצף, ללא מסגרות.
    לחיצה על מילה מציגה את עדי הנוסח שלה בפאנל הצדדי.
    """
    word_clicked = pyqtSignal(int)  # emits word index

    def __init__(self, words_data: list, main_witness: str, parent=None):
        """
        words_data: רשימת dict, כל אחד עם 'section' ו-'witnesses'
        main_witness: שם עד הנוסח הראשי (וילנא)
        """
        super().__init__(parent)
        self.words_data = words_data
        self.main_witness = main_witness
        self.selected_idx = -1

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet("background-color:#F0F4F7;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 14, 18, 20)
        outer.setSpacing(0)

        self._flow_widget = _FlowWidget(words_data, main_witness)
        self._flow_widget.word_clicked.connect(self.word_clicked.emit)
        outer.addWidget(self._flow_widget)
        outer.addStretch()

    def select_word(self, idx: int):
        self._flow_widget.select_word(idx)
        self.selected_idx = idx

    def clear_selection(self):
        self._flow_widget.select_word(-1)
        self.selected_idx = -1
