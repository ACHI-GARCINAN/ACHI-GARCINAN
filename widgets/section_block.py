from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor

from utils import build_vilna_diff_html


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

        self._normal_style   = "QFrame#section_block{background-color:#FFFFFF;border:1px solid #CBD5E0;border-radius:8px;margin:3px 8px;}"
        self._hover_style    = "QFrame#section_block{background-color:#F7FAFC;border:1px solid #A0B4CC;border-right:4px solid #5A6A82;border-radius:8px;margin:3px 8px;}"
        self._selected_style = "QFrame#section_block{background-color:#EBF4FF;border:1px solid #5A6A82;border-right:4px solid #2D3748;border-radius:8px;margin:3px 8px;}"
        self._diff_style     = "QFrame#section_block{background-color:#FFF5F5;border:1px solid #E53E3E;border-right:4px solid #C53030;border-radius:8px;margin:3px 8px;}"

        self.setObjectName("section_block")
        self.setStyleSheet(self._normal_style)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 10, 16, 12)
        self._layout.setSpacing(6)

        tag = QLabel(section['section'])
        tag.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        tag.setStyleSheet("color:#4A5568;background-color:#EDF2F7;border-radius:4px;padding:2px 8px;")
        tag.setAlignment(Qt.AlignmentFlag.AlignRight)
        tag.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._layout.addWidget(tag, alignment=Qt.AlignmentFlag.AlignRight)

        text = section['witnesses'].get(main_witness, '') or ''
        if text == 'None':
            text = ''
        self._plain_text = text

        self._text_lbl = QLabel(text if text else '(אין טקסט)')
        self._text_lbl.setWordWrap(True)
        self._text_lbl.setFont(QFont("David", 16))
        self._text_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self._text_lbl.setStyleSheet("color:#2D3748;background:transparent;")
        self._layout.addWidget(self._text_lbl)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    def show_witness_diff(self, witness_name: str):
        if self._active_diff_witness == witness_name:
            self._active_diff_witness = None
            self._text_lbl.setTextFormat(Qt.TextFormat.AutoText)
            self._text_lbl.setText(self._plain_text if self._plain_text else '(אין טקסט)')
            self.setStyleSheet(self._selected_style if self.is_selected else self._normal_style)
            return

        self._active_diff_witness = witness_name
        witness_text = self.section['witnesses'].get(witness_name, '') or ''
        if witness_text == 'None':
            witness_text = ''

        if self._plain_text and witness_text:
            html = build_vilna_diff_html(self._plain_text, witness_text)
            self._text_lbl.setTextFormat(Qt.TextFormat.RichText)
            self._text_lbl.setText(
                f'<div dir="rtl" style="font-family:David,serif;font-size:16pt;color:#2D3748;">{html}</div>'
            )
        self.setStyleSheet(self._diff_style)

    def clear_diff(self):
        self._active_diff_witness = None
        self._text_lbl.setTextFormat(Qt.TextFormat.AutoText)
        self._text_lbl.setText(self._plain_text if self._plain_text else '(אין טקסט)')
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
