"""
SearchSpinner - אנימציה של חיפוש בחלון מרכזי
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QSize, QRect
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray


class SearchSpinner(QWidget):
    """
    אנימציה של ספינר חיפוש שמופיעה במרכז המסך.
    שימוש:
        spinner = SearchSpinner(parent_window)
        spinner.show()
        # ... חיפוש ...
        spinner.hide()
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background:transparent;")
        
        self._rotation = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_rotate)
        self._timer.setInterval(30)  # 30ms per frame = smooth animation
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # אזור ספינר
        self._spinner_lbl = QLabel()
        self._spinner_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spinner_lbl.setFixedSize(60, 60)
        layout.addWidget(self._spinner_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # טקסט
        self._text_lbl = QLabel("חיפוש במילון...")
        self._text_lbl.setFont(QFont("David", 12))
        self._text_lbl.setStyleSheet("color:#C8A060;background:transparent;")
        self._text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._text_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # רקע חצי שקוף
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 100);
                border-radius: 16px;
            }
        """)
        
        self.setFixedSize(200, 160)
    
    def _on_rotate(self):
        """סובב את הספינר כל 30ms"""
        self._rotation = (self._rotation + 6) % 360
        pixmap = self._create_spinner_pixmap()
        self._spinner_lbl.setPixmap(pixmap)
    
    def _create_spinner_pixmap(self) -> QPixmap:
        """יוצר SVG spinner עם rotation"""
        svg_str = f"""
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <g transform="rotate({self._rotation} 50 50)">
                <circle cx="50" cy="15" r="8" fill="#C8A060" opacity="1"/>
                <circle cx="85" cy="25" r="7" fill="#C8A060" opacity="0.9"/>
                <circle cx="92" cy="60" r="6" fill="#C8A060" opacity="0.7"/>
                <circle cx="85" cy="85" r="5" fill="#C8A060" opacity="0.5"/>
                <circle cx="50" cy="95" r="4" fill="#C8A060" opacity="0.3"/>
            </g>
        </svg>
        """
        
        svg_bytes = QByteArray(svg_str.strip().encode("utf-8"))
        renderer = QSvgRenderer(svg_bytes)
        
        pixmap = QPixmap(60, 60)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
        
        return pixmap
    
    def showEvent(self, event):
        """מתחיל אנימציה כשהחלון מופיע"""
        super().showEvent(event)
        self._timer.start()
        self._center_on_parent()
    
    def hideEvent(self, event):
        """מעצור אנימציה כשהחלון נסגר"""
        super().hideEvent(event)
        self._timer.stop()
    
    def _center_on_parent(self):
        """מרכז את הספינר על הורה"""
        if self.parent():
            parent_rect = self.parent().rect()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)
    
    def set_text(self, text: str):
        """שינוי טקסט האנימציה"""
        self._text_lbl.setText(text)
