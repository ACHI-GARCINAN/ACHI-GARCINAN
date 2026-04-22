from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor

from utils import build_highlighted_html


class WitnessCard(QFrame):
    clicked = pyqtSignal(str)  # emits witness name

    def __init__(self, name: str, text, color_pair: tuple,
                 base_text: str = '', highlight: bool = False,
                 clickable: bool = False, is_html: bool = False,
                 font_family: str = 'David', font_size: int = 15,
                 hide_minor: bool = False,
                 parent=None):
        super().__init__(parent)
        self.accent, self.bg = color_pair
        self.witness_name = name
        self.clickable = clickable
        self.text = text
        self.base_text = base_text
        self.highlight = highlight
        self.is_html = is_html
        self._font_family = font_family
        self._font_size = font_size
        self.hide_minor = hide_minor
        
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        if clickable and text:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.setObjectName("witness_card")
        self._apply_style()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 10, 14, 12)
        self.layout.setSpacing(6)

        self.name_lbl = QLabel(name)
        self.name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.name_lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.layout.addWidget(self.name_lbl)

        self.text_lbl = QLabel()
        self.text_lbl.setWordWrap(True)
        self.text_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.text_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.text_lbl.setFont(QFont(font_family, font_size))
        self.text_lbl.setTextFormat(Qt.TextFormat.RichText)
        self.text_lbl.setStyleSheet("background:transparent;")
        self.layout.addWidget(self.text_lbl)
        
        self._update_content()

    def _apply_style(self):
        if self.text:
            self.setStyleSheet(
                f"QFrame#witness_card{{background-color:{self.bg};border:1px solid #CBD5E0;"
                f"border-top:3px solid {self.accent};border-radius:10px;margin:4px 8px;}}"
            )
            if hasattr(self, 'name_lbl'):
                self.name_lbl.setStyleSheet(
                    f"color:{self.accent};background:transparent;"
                    f"border:1px solid {self.accent};border-radius:5px;padding:3px 8px;"
                )
        else:
            self.setStyleSheet(
                "QFrame#witness_card{background-color:#EBF0F5;border:1px dashed #CBD5E0;"
                "border-radius:10px;margin:4px 8px;}"
            )
            if hasattr(self, 'name_lbl'):
                self.name_lbl.setStyleSheet(
                    "color:#718096;background:transparent;"
                    "border:1px solid #CBD5E0;border-radius:5px;padding:3px 8px;"
                )

    def _update_content(self):
        if self.text:
            if self.is_html:
                self.text_lbl.setText(self.text)
            elif self.highlight and self.base_text:
                # We'll need to pass hide_minor here. Let's add it to WitnessCard.
                html_content = build_highlighted_html(self.text, self.base_text, hide_minor=getattr(self, 'hide_minor', False))
                self.text_lbl.setText(
                    f'<div dir="rtl" style="font-family:{self._font_family},serif;font-size:{self._font_size}pt;'
                    f'color:#2D3748;text-align:justify;">{html_content}</div>'
                )
            else:
                display = self.text if self.text else '(אין טקסט)'
                self.text_lbl.setText(
                    f'<div dir="rtl" style="font-family:{self._font_family},serif;'
                    f'font-size:{self._font_size}pt;color:#2D3748;text-align:justify;">{display}</div>'
                )
        else:
            self.text_lbl.setText('<div dir="rtl" style="color:#A0AEC0;font-style:italic;font-size:12px;">אין עד נוסח לקטע זה</div>')
        
        self._apply_style()

    def update_theme(self, color_pair: tuple, font_family: str, font_size: int, hide_minor: bool = None):
        self.accent, self.bg = color_pair
        self._font_family = font_family
        self._font_size = font_size
        if hide_minor is not None:
            self.hide_minor = hide_minor
        self._update_content()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.clickable:
            self.clicked.emit(self.witness_name)
        super().mousePressEvent(event)
