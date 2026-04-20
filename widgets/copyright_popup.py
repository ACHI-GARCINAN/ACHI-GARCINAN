import os
import sys

from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QApplication, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QColor, QCursor, QDesktopServices


class CopyrightPopup(QWidget):
    """
    פופ-אפ overlay: מכסה את כל חלון-האב בשכבה שקופה למחצה,
    במרכזה מלבן עם קצוות מעוגלים. לחיצה מחוץ למלבן → סגירה.
    """
    MAIL = "talmud1239@gmail.com"

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setGeometry(parent.rect())
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        is_colorful = False
        if parent and hasattr(parent, 'window'):
            win = parent.window()
            if hasattr(win, '_theme'):
                is_colorful = (win._theme == 'colorful')


        card_bg     = "#FFFFFF" if not is_colorful else "#2B1A0F"
        card_border = "#A0B4CC" if not is_colorful else "#C8A060"
        title_color = "#2D3748" if not is_colorful else "#FFF5E6"
        body_color  = "#2D3748" if not is_colorful else "#F0DFC0"
        sep_color   = "#CBD5E0" if not is_colorful else "#7A5030"
        contact_color = "#4A5568" if not is_colorful else "#C8A87A"
        
        self._card = QFrame(self)
        self._card.setObjectName("popup_frame")
        self._card.setStyleSheet(f"""
            QFrame#popup_frame {{
                background-color: {card_bg};
                border: 2px solid {card_border};
                border-radius: 16px;
            }}
        """)
        self._card.setFixedWidth(480)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(35)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 5)
        self._card.setGraphicsEffect(shadow)

        inner = QVBoxLayout(self._card)
        inner.setContentsMargins(30, 26, 30, 26)
        inner.setSpacing(14)

        title = QLabel("הערת שימוש")
        title.setFont(QFont("David", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{title_color};background:transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background:{sep_color};max-height:1px;border:none;")
        inner.addWidget(sep)

        body = QLabel(
            "שים לב כי כל החומר כאן לוקט מתוכן השייך משפטית לאתר\n"
            "\u201cפרידברג \u2013 הכי גרסינן\u201d,\n\n"
            "והשימוש בו מותר אך ורק לצורך שימוש פרטי ולא לצורך מסחרי!"
        )
        body.setFont(QFont("David", 13))
        body.setStyleSheet(f"color:{body_color};background:transparent;")
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)
        inner.addWidget(body)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"background:{sep_color};max-height:1px;border:none;")
        inner.addWidget(sep2)

        contact_row = QHBoxLayout()
        contact_row.setSpacing(6)

        contact_lbl = QLabel("תגובות והערות ניתן לכתוב במייל")
        contact_lbl.setFont(QFont("David", 12))
        contact_lbl.setStyleSheet(f"color:{contact_color};background:transparent;")
        contact_row.addWidget(contact_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        mail_btn = QPushButton(self.MAIL)
        mail_btn.setFont(QFont("Arial", 11))
        mail_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        mail_btn.setStyleSheet("""
            QPushButton {
                color:#1A5E8A; background:transparent;
                border:none; padding:0; text-decoration:underline;
            }
            QPushButton:hover { color:#0A3E6A; }
        """)
        mail_btn.clicked.connect(self._open_mail)
        contact_row.addWidget(mail_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        copy_btn = QPushButton("📋")
        copy_btn.setToolTip("העתק כתובת מייל")
        copy_btn.setFixedSize(26, 26)
        copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        copy_btn.setFont(QFont("Arial", 13))
        copy_btn.setStyleSheet("""
            QPushButton { background:transparent; border:none; padding:0; }
            QPushButton:hover { background:rgba(0,0,0,0.07); border-radius:5px; }
        """)
        copy_btn.clicked.connect(self._copy_mail)
        contact_row.addWidget(copy_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        contact_row.addStretch()
        inner.addLayout(contact_row)

        card_layout = QVBoxLayout(self)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self._card, 0, Qt.AlignmentFlag.AlignCenter)

        self.raise_()
        self.show()

    def _open_mail(self):
        if sys.platform == "win32":
            os.startfile(f"mailto:{self.MAIL}")
        else:
            QDesktopServices.openUrl(QUrl(f"mailto:{self.MAIL}"))

    def _copy_mail(self):
        QApplication.clipboard().setText(self.MAIL)
        sender = self.sender()
        sender.setText("✓")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1200, lambda: sender.setText("📋"))

    def mousePressEvent(self, event):
        if not self._card.geometry().contains(event.position().toPoint()):
            self.close()
        else:
            super().mousePressEvent(event)

    def exec(self):
        from PyQt6.QtCore import QEventLoop
        loop = QEventLoop()
        self.destroyed.connect(loop.quit)
        loop.exec()

    def close(self):
        super().close()
        self.deleteLater()