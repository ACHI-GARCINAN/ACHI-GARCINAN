import sys
import os
import time
from PyQt6.QtWidgets import QApplication, QSplashScreen, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont

from db import load_masechet_list, get_base_dir
from main_window import MainWindow, get_icon

def resource_path(relative_path):
    """ מחזירה את הנתיב המוחלט לקובץ, עובד גם ב-EXE וגם ב-App """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class TalmudApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self._main_window = None

    def set_main_window(self, window):
        self._main_window = window

    def notify(self, obj, event):
        if (self._main_window is not None and event.type() == QEvent.Type.KeyPress):
            mods = event.modifiers()
            key  = event.key()
            _M_KEYS = (Qt.Key.Key_M, Qt.Key(0x05DE), Qt.Key(0x05E6))
            is_alt_pressed = bool(mods & Qt.KeyboardModifier.AltModifier)
            if is_alt_pressed and key in _M_KEYS:
                btn = self._main_window.mode_btn
                btn.setChecked(not btn.isChecked())
                return True
        return super().notify(obj, event)

def main():
    # 1. סינון ארגומנטים של macOS
    args = [arg for arg in sys.argv if not arg.startswith("-psn")]

    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("talmud.synopsis.viewer.1")

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = TalmudApp(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    QApplication.setStyle("Fusion")

    icon = get_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    # ── Splash Screen ──
    splash_pix = QPixmap(500, 300)
    splash_pix.fill(QColor("#F7F3EC"))
    painter = QPainter(splash_pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor("#C8A060"))
    painter.drawRoundedRect(10, 10, 480, 280, 16, 16)
    painter.setPen(QColor("#5A1A00"))
    painter.setFont(QFont("David", 28, QFont.Weight.Bold))
    painter.drawText(splash_pix.rect(), Qt.AlignmentFlag.AlignCenter, "נוסחאות התלמוד")
    painter.end()

    splash = QSplashScreen(splash_pix)
    splash.show()
    app.processEvents()

    # ── טעינת נתונים ──
    if len(args) > 1:
        folder = args[1]
    else:
        folder = resource_path("")

    masechtot = load_masechet_list(folder)
    
    if not masechtot:
        folder = QFileDialog.getExistingDirectory(None, "בחר תיקייה עם talmud.db", "")
        if folder:
            masechtot = load_masechet_list(folder)

    if not masechtot:
        QMessageBox.critical(None, "שגיאה", "לא נמצא קובץ talmud.db.")
        sys.exit(1)

    window = MainWindow(masechtot)
    app.set_main_window(window)
    window.show()
    splash.finish(window)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()