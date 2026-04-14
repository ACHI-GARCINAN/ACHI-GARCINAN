from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QSizePolicy, QGraphicsDropShadowEffect, QTextBrowser
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor

from utils import build_highlighted_html


class WitnessCard(QFrame):
    clicked = pyqtSignal(str)  # emits witness name

    def __init__(self, name: str, text, color_pair: tuple,
                 base_text: str = '', highlight: bool = False,
                 clickable: bool = False, parent=None):
        super().__init__(parent)
        accent, bg = color_pair
        self.witness_name = name
        self.clickable = clickable
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        if clickable and text:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        if text:
            self.setStyleSheet(
                f"QFrame{{background-color:{bg};border:1px solid {accent}35;"
                f"border-top:3px solid {accent};border-radius:10px;margin:4px 8px;}}"
            )
        else:
            self.setStyleSheet(
                "QFrame{background-color:#F0EDE6;border:1px dashed #C5B89A;"
                "border-radius:10px;margin:4px 8px;}"
            )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(6)

        name_lbl = QLabel(name)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        name_lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        if text:
            name_lbl.setStyleSheet(
                f"color:{accent};background:transparent;"
                f"border:1px solid {accent};border-radius:5px;padding:3px 8px;"
            )
        else:
            name_lbl.setStyleSheet(
                "color:#A09080;background:transparent;"
                "border:1px solid #C5B89A;border-radius:5px;padding:3px 8px;"
            )
        layout.addWidget(name_lbl)

        if text:
            if highlight and base_text:
                html_content = build_highlighted_html(text, base_text)
                txt_widget = QTextBrowser()
                txt_widget.setOpenLinks(False)
                txt_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                txt_widget.setHtml(
                    f'<div dir="rtl" style="font-family:David,serif;font-size:15pt;'
                    f'color:#1A0A00;text-align:right;">{html_content}</div>'
                )
                txt_widget.setStyleSheet("QTextBrowser{background:transparent;border:none;color:#1A0A00;}")
                txt_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
                txt_widget.document().adjustSize()
                h = int(txt_widget.document().size().height()) + 16
                txt_widget.setFixedHeight(max(50, h))
                layout.addWidget(txt_widget)
            else:
                txt_lbl = QLabel(text)
                txt_lbl.setWordWrap(True)
                txt_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
                txt_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                txt_lbl.setFont(QFont("David", 15))
                txt_lbl.setStyleSheet("color:#1A0A00;background:transparent;")
                layout.addWidget(txt_lbl)
        else:
            miss = QLabel("אין עד נוסח לקטע זה")
            miss.setAlignment(Qt.AlignmentFlag.AlignRight)
            miss.setStyleSheet("color:#B0A090;font-style:italic;font-size:12px;background:transparent;")
            layout.addWidget(miss)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 18))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.clickable:
            self.clicked.emit(self.witness_name)
        super().mousePressEvent(event)
