from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QCheckBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from styles import WITNESS_COLORS
from widgets.witness_card import WitnessCard


class WitnessPanel(QWidget):
    witness_clicked = pyqtSignal(str)

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

        header_widget = QWidget()
        header_widget.setStyleSheet("background-color:#3A2010;border-bottom:2px solid #C8A060;")
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(16, 10, 16, 8)
        header_layout.setSpacing(5)

        self.header = QLabel("בחר קטע לעדי נוסח")
        self.header.setFont(QFont("David", 14, QFont.Weight.Bold))
        self.header.setStyleSheet("color:#F0DFC0;background:transparent;border:none;")
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
        self.highlight_diffs = bool(state)
        self.hint_label.setVisible(self.highlight_diffs)
        if self._current_section is not None:
            self.show_section(self._current_section, self._current_page, self._base_text)

    def _on_hide_empty_changed(self, state):
        self.hide_empty_witnesses = bool(state)
        if self._current_section is not None:
            self.show_section(self._current_section, self._current_page, self._base_text)

    def _show_placeholder(self):
        ph = QLabel("←  לחץ על קטע בטקסט\nכדי לראות את עדי הנוסח")
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

    def reset(self):
        self._current_section = None
        self._current_page = ''
        self._base_text = ''
        self._clear()
        self.header.setText("בחר קטע לעדי נוסח")
        self._show_placeholder()
