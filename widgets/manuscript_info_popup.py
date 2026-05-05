import sys
import os

from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QApplication, QGraphicsDropShadowEffect, QScrollArea
)
from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtGui import QFont, QColor, QCursor, QDesktopServices


class ManuscriptInfoPopup(QWidget):
    """
    פופ-אפ overlay: מציג מידע על כתב יד.
    מכסה את כל חלון-האב בשכבה שקופה למחצה,
    במרכזה מלבן עם קצוות מעוגלים. לחיצה מחוץ למלבן → סגירה.
    """

    def __init__(self, manuscript_name: str, manuscript_text: str, parent: QWidget):
        super().__init__(parent)
        self.setGeometry(parent.rect())
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._card = QFrame(self)
        self._card.setObjectName("manuscript_popup_frame")
        self._card.setStyleSheet("""
            QFrame#manuscript_popup_frame {
                background-color: #F5F1ED;
                border: 2px solid #8B7355;
                border-radius: 16px;
            }
        """)
        self._card.setFixedWidth(520)
        self._card.setMaximumHeight(600)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(35)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 5)
        self._card.setGraphicsEffect(shadow)

        inner = QVBoxLayout(self._card)
        inner.setContentsMargins(24, 20, 24, 20)
        inner.setSpacing(12)

        # כותרת
        title = QLabel(f"📜 {manuscript_name}")
        title.setFont(QFont("David", 14, QFont.Weight.Bold))
        title.setStyleSheet("color:#4A3728;background:transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignRight)
        title.setWordWrap(True)
        inner.addWidget(title)

        # קו הפרדה
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:#C9B8A8;max-height:1px;border:none;")
        inner.addWidget(sep)

        # אזור גלילה עם הטקסט
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #FEFBF8;
                border: 1px solid #E8DDD0;
                border-radius: 8px;
            }
            QScrollBar:vertical {
                background-color: #F5F1ED;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #C9B8A8;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #B8A897;
            }
        """)

        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(12, 12, 12, 12)

        body = QLabel(manuscript_text)
        body.setFont(QFont("David", 11))
        body.setStyleSheet("color:#2D2416;background:transparent;")
        body.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_layout.addWidget(body)
        text_layout.addStretch()

        scroll.setWidget(text_widget)
        inner.addWidget(scroll, 1)

        # כפתורים בתחתית
        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        close_btn = QPushButton("סגור")
        close_btn.setFont(QFont("David", 11))
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B7355;
                color: #FFFBF7;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7A6349;
            }
            QPushButton:pressed {
                background-color: #6B5540;
            }
        """)
        close_btn.clicked.connect(self.close)
        button_row.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignLeft)

        button_row.addStretch()
        inner.addLayout(button_row)

        card_layout = QVBoxLayout(self)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self._card, 0, Qt.AlignmentFlag.AlignCenter)

        self.raise_()
        self.show()

    def mousePressEvent(self, event):
        if not self._card.geometry().contains(event.position().toPoint()):
            self.close()
        else:
            super().mousePressEvent(event)

    def exec(self):
        loop = __import__('PyQt6.QtCore', fromlist=['QEventLoop']).QEventLoop()
        self.destroyed.connect(loop.quit)
        loop.exec()

    def close(self):
        super().close()
        self.deleteLater()
