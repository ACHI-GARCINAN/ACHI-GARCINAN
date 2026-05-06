"""
נוסחאות התלמוד - מציג עדי נוסח
הרצה: python main.py [נתיב_לתיקיה_עם_talmud.db]
"""
import time
import sys
import os
import ctypes
from main_window import MainWindow, get_icon
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QIcon
from db import load_masechet_list, get_base_dir

class TalmudApp(QApplication):
    """מחלקת אפליקציה מותאמת — מיירטת קיצורי מקלדת גלובליים דרך notify()."""

    def __init__(self, argv):
        super().__init__(argv)
        self._main_window = None

    def set_main_window(self, window):
        self._main_window = window

    def notify(self, obj, event):
        if (self._main_window is not None
                and event.type() == QEvent.Type.KeyPress):
            mods = event.modifiers()
            key  = event.key()
            
            # זיהוי מקש M/מ/צ:
            # Key_M (77) = אנגלית
            # 0x05DE = מ (mem) בעברית
            # 0x05E6 = צ (tsadi) בעברית (במקלדות מסוימות)
            _M_KEYS = (Qt.Key.Key_M, Qt.Key(0x05DE), Qt.Key(0x05E6))
            
            # בדיקה אם מקש Alt לחוץ. 
            # ב-Windows, Alt ימני (AltGr) עשוי להופיע כ-ControlModifier | AltModifier.
            # לכן נבדוק אם AltModifier קיים ב-modifiers.
            is_alt_pressed = bool(mods & Qt.KeyboardModifier.AltModifier)
            
            # גיבוי נוסף: בדיקת ה-ScanCode הפיזי של מקש M (בדרך כלל 50 ב-Windows/Linux ל-M)
            # זה עוזר כשהמיפוי הלוגי של המקש משתנה בגלל שפת המקלדת.
            is_m_physical = (event.nativeScanCode() in (50, 0x32)) # 50 עשוי להשתנות בין מערכות, אך נפוץ ל-M

            if is_alt_pressed and (key in _M_KEYS or is_m_physical):
                btn = self._main_window.mode_btn
                btn.setChecked(not btn.isChecked())
                return True
                
        return super().notify(obj, event)


def main():
    if sys.platform == "win32":
        my_app_id = "talmud.synopsis.viewer.v1" 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(my_app_id)

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = TalmudApp(sys.argv)
    
    # טעינת האייקון והגדרה לאפליקציה (עבור שורת המשימות/Dock)
    icon = get_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
        
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    QApplication.setStyle("Fusion")

    # ── Splash Screen ──────────────────────────────────────
    from PyQt6.QtWidgets import QSplashScreen
    from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont

    splash_pix = QPixmap(500, 300)
    splash_pix.fill(QColor("#F7F3EC"))
    painter = QPainter(splash_pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # מסגרת
    painter.setPen(QColor("#C8A060"))
    painter.drawRoundedRect(10, 10, 480, 280, 16, 16)

    # כותרת
    painter.setPen(QColor("#5A1A00"))
    painter.setFont(QFont("David", 28, QFont.Weight.Bold))
    painter.drawText(splash_pix.rect(), Qt.AlignmentFlag.AlignCenter, "נוסחאות התלמוד")

    # כיתוב טעינה
    painter.setPen(QColor("#C8A060"))
    painter.setFont(QFont("David", 14))
    painter.drawText(0, 240, 500, 40, Qt.AlignmentFlag.AlignCenter, "טוען נתונים...")

    painter.end()

    splash = QSplashScreen(splash_pix)
    splash.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()
    # ───────────────────────────────────────────────────────

    t0 = time.time()
    folder = sys.argv[1] if len(sys.argv) > 1 else get_base_dir()
    masechtot = load_masechet_list(folder)
    print(f"load_masechet_list: {time.time()-t0:.2f}s")
    t0 = time.time()
    
    if not masechtot:
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(None, "בחר תיקייה", "")
        if not folder:
            sys.exit(0)
        masechtot = load_masechet_list(folder)

    if not masechtot:
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "שגיאה", "לא נמצא קובץ talmud.db בתיקייה.")
        sys.exit(1)

    window = MainWindow(masechtot)
    print(f"MainWindow init: {time.time()-t0:.2f}s")
    app.set_main_window(window)
    window.showMaximized()
    
    splash.finish(window)  # מסתיר את הספלאש כשהחלון מוכן

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
