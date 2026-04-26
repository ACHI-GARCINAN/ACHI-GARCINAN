import sys
import os
import time
from PyQt6.QtWidgets import QApplication, QSplashScreen, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont

from db import load_masechet_list, get_base_dir
from main_window import MainWindow, get_icon

# הפונקציה הזו היא ההבדל בין הצלחה לכישלון באריזה
def resource_path(relative_path):
    """ מוצאת את הקובץ גם אם הוא בתוך ה-EXE וגם אם הוא בתיקיית פיתוח """
    try:
        # PyInstaller יוצר תיקייה זמנית בכתובת הזו
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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
    # סינון ארגומנטים של macOS
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

    # ── Splash Screen (המקורי שלך - לא נגעתי בעיצוב!) ──
    splash_pix = QPixmap(500, 300)
    splash_pix.fill(QColor("#F7F3EC"))
    painter = QPainter(splash_pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor("#C8A060"))
    painter.drawRoundedRect(10, 10, 480, 280, 16, 16)
    painter.setPen(QColor("#5A1A00"))
    painter.setFont(QFont("David", 28, QFont.Weight.Bold))
    painter.drawText(splash_pix.rect(), Qt.AlignmentFlag.AlignCenter, "נוסחאות התלמוד")
    painter.setPen(QColor("#C8A060"))
    painter.setFont(QFont("David", 14))
    painter.drawText(0, 240, 500, 40, Qt.AlignmentFlag.AlignCenter, "טוען נתונים...")
    painter.end()

    splash = QSplashScreen(splash_pix)
    splash.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    # ── טעינת הנתונים - התיקון הקריטי ──
    # מחפש קודם כל בתיקייה שבה נמצא ה-EXE/סקריפט
    folder = args[1] if len(args) > 1 else resource_path("")
    
    # טעינה
    masechtot = load_masechet_list(folder)
    
    # אם עדיין לא מצא, פתח חלונית לבחירה ידנית
    if not masechtot:
        folder = QFileDialog.getExistingDirectory(None, "בחר תיקייה עם talmud.db", "")
        if folder:
            masechtot = load_masechet_list(folder)

    # אם גם זה לא עבד - הודעת שגיאה וסגירה
    if not masechtot:
        QMessageBox.critical(None, "שגיאה", "לא נמצא קובץ הנתונים talmud.db.")
        sys.exit(1)

    window = MainWindow(masechtot)
    app.set_main_window(window)
    window.show()
    splash.finish(window)
    sys.exit(app.exec())

if __name__ == '__main__':
    main()