import sys
import os
import time

# ייבוא מינימליסטי בלבד להתחלה
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont

class TalmudApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self._main_window = None

    def set_main_window(self, window):
        self._main_window = window

    def notify(self, obj, event):
        if (self._main_window is not None and event.type() == QEvent.Type.KeyPress):
            mods = event.modifiers()
            key = event.key()
            if bool(mods & Qt.KeyboardModifier.AltModifier) and (key in (Qt.Key.Key_M, Qt.Key(0x05DE), Qt.Key(0x05E6))):
                self._main_window.mode_btn.setChecked(not self._main_window.mode_btn.isChecked())
                return True
        return super().notify(obj, event)

def main():
    # 1. הגדרות מערכת בסיסיות (מהיר מאוד)
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("talmud.synopsis.viewer.1")

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = TalmudApp(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    
    # 2. הצגת Splash Screen מיד! (לפני כל ה-Imports הכבדים)
    splash_pix = QPixmap(500, 300)
    splash_pix.fill(QColor("#F7F3EC"))
    painter = QPainter(splash_pix)
    painter.setPen(QColor("#C8A060"))
    painter.drawRoundedRect(10, 10, 480, 280, 16, 16)
    painter.setPen(QColor("#5A1A00"))
    painter.setFont(QFont("David", 28, QFont.Weight.Bold))
    painter.drawText(splash_pix.rect(), Qt.AlignmentFlag.AlignCenter, "נוסחאות התלמוד")
    painter.end()
    
    splash = QSplashScreen(splash_pix)
    splash.show()
    app.processEvents() # גורם ל-Splash להופיע מיד על המסך

    # 3. עכשיו עושים את ה-Imports הכבדים כשהמשתמש כבר רואה משהו
    from db import load_masechet_list, get_base_dir
    from main_window import MainWindow, get_icon
    
    # הגדרת אייקון
    icon = get_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    # 4. טעינת נתונים
    folder = sys.argv[1] if len(sys.argv) > 1 else get_base_dir()
    masechtot = load_masechet_list(folder)
    
    if not masechtot:
        from PyQt6.QtWidgets import QFileDialog
        splash.hide() # מחביאים את ה-Splash אם צריך לבחור תיקייה
        folder = QFileDialog.getExistingDirectory(None, "בחר תיקייה", "")
        if not folder: sys.exit(0)
        masechtot = load_masechet_list(folder)
        splash.show()

    # 5. הקמת החלון הראשי
    window = MainWindow(masechtot)
    app.set_main_window(window)
    window.show()
    
    splash.finish(window)
    sys.exit(app.exec())

if __name__ == '__main__':
    main()