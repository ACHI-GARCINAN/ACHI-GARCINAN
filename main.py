"""
סינופסיס תלמוד בבלי - מציג עדי נוסח
הרצה: python main.py [נתיב_לתיקיה_עם_talmud.db]
"""

import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from db import load_masechet_list, get_base_dir
from main_window import MainWindow, get_icon

def main():
    if sys.platform == "win32":
        import ctypes
        # חיוני לאייקון בשורת המשימות
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "talmud.synopsis.viewer.1"
        )

    # תיקון בעיית DPI ויקיצה משינה
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    icon = get_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    folder = sys.argv[1] if len(sys.argv) > 1 else get_base_dir()
    masechtot = load_masechet_list(folder)

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
    # חיוני: הגדר אייקון גם ישירות על החלון אחרי היצירה
    if not icon.isNull():
        window.setWindowIcon(icon)
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
