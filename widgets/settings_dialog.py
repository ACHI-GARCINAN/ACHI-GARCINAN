"""
דיאלוג הגדרות - בחירת גופן, גודל וערכת נושא
"""
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFrame, QWidget, QLineEdit, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QFontDatabase, QIntValidator, QPixmap


def get_hebrew_fonts() -> list:
    """מחזיר רשימת גופנים שתומכים בעברית, ממוין לפי שם."""
    try:
        all_families = QFontDatabase.families()
    except Exception:
        all_families = []

    hebrew_fonts = []
    for family in all_families:
        try:
            writing_systems = QFontDatabase.writingSystems(family)
            if QFontDatabase.WritingSystem.Hebrew in writing_systems:
                hebrew_fonts.append(family)
        except Exception:
            pass

    if not hebrew_fonts:
        fallback = ['David', 'Frank Ruehl', 'FrankRuehl', 'Miriam', 'Narkisim',
                    'Rod', 'Levenim MT', 'Arial', 'Times New Roman']
        known = set(all_families)
        for f in fallback:
            if not known or f in known:
                hebrew_fonts.append(f)

    return sorted(set(hebrew_fonts))


class SettingsDialog(QDialog):
    # font_family, font_size, theme_name
    settings_changed = pyqtSignal(str, int, str)

    def __init__(self, current_font: str, current_size: int, current_theme: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("הגדרות תצוגה")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumWidth(500)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog { background-color: #F0F4F7; }
            QLabel { color: #2D3748; }
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E0;
                border-radius: 6px;
                padding: 5px 10px;
                color: #2D3748;
                font-size: 13px;
                min-height: 30px;
            }
            QComboBox:focus { border-color: #5A6A82; }
            QComboBox::drop-down { border: none; padding-left: 5px; }
            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E0;
                border-radius: 6px;
                padding: 4px 8px;
                color: #2D3748;
                font-size: 14px;
                min-height: 30px;
            }
            QLineEdit:focus { border-color: #5A6A82; }
            QPushButton#ok_btn {
                background-color: #5A6A82;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#ok_btn:hover { background-color: #4A5A72; }
            QPushButton#cancel_btn {
                background-color: #E1E8ED;
                color: #4A5568;
                border: 1px solid #CBD5E0;
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 13px;
            }
            QPushButton#cancel_btn:hover { background-color: #D1D9E0; }
            QPushButton#size_btn {
                background-color: #E1E8ED;
                color: #2D3748;
                border: 1px solid #CBD5E0;
                border-radius: 6px;
                min-width: 38px;
                min-height: 34px;
                font-weight: bold;
            }
            QPushButton#size_btn:hover {
                background-color: #CBD5E0;
                border-color: #5A6A82;
            }
            QPushButton#size_btn:pressed { background-color: #A0B4CC; }
            
            QRadioButton {
                color: #2D3748;
                font-size: 13px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # כותרת
        title = QLabel("הגדרות תצוגה")
        title.setFont(QFont("David", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #CBD5E0;")
        layout.addWidget(sep)

        # ── שורת גופן ──
        font_row = QWidget()
        font_layout = QHBoxLayout(font_row)
        font_layout.setContentsMargins(0, 0, 0, 0)
        font_layout.setSpacing(12)

        font_label = QLabel("גופן:")
        font_label.setFont(QFont("David", 13))
        font_label.setFixedWidth(85)
        font_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.font_combo = QComboBox()
        self.font_combo.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        hebrew_fonts = get_hebrew_fonts()
        if not hebrew_fonts:
            hebrew_fonts = ['David']

        for f in hebrew_fonts:
            self.font_combo.addItem(f)
            idx = self.font_combo.count() - 1
            self.font_combo.setItemData(idx, QFont(f, 12), Qt.ItemDataRole.FontRole)

        idx = self.font_combo.findText(current_font)
        if idx >= 0:
            self.font_combo.setCurrentIndex(idx)

        self.font_combo.currentTextChanged.connect(self._update_preview)

        font_layout.addWidget(self.font_combo, 1)
        font_layout.addWidget(font_label)
        layout.addWidget(font_row)

        # ── שורת גודל גופן ──
        self._font_size = current_size

        size_row = QWidget()
        size_layout = QHBoxLayout(size_row)
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.setSpacing(8)

        size_label = QLabel("גודל גופן:")
        size_label.setFont(QFont("David", 13))
        size_label.setFixedWidth(85)
        size_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.btn_smaller = QPushButton("א")
        self.btn_smaller.setObjectName("size_btn")
        self.btn_smaller.setFont(QFont("David", 11))
        self.btn_smaller.setFixedSize(38, 34)
        self.btn_smaller.setToolTip("הקטן גופן")
        self.btn_smaller.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_smaller.clicked.connect(self._decrease_size)

        self.size_edit = QLineEdit(str(current_size))
        self.size_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.size_edit.setFixedWidth(52)
        self.size_edit.setFixedHeight(34)
        self.size_edit.setValidator(QIntValidator(8, 36, self))
        self.size_edit.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.size_edit.textChanged.connect(self._on_size_text_changed)

        self.btn_larger = QPushButton("א")
        self.btn_larger.setObjectName("size_btn")
        self.btn_larger.setFont(QFont("David", 17, QFont.Weight.Bold))
        self.btn_larger.setFixedSize(38, 34)
        self.btn_larger.setToolTip("הגדל גופן")
        self.btn_larger.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_larger.clicked.connect(self._increase_size)

        size_layout.addWidget(self.btn_larger)
        size_layout.addWidget(self.size_edit)
        size_layout.addWidget(self.btn_smaller)
        size_layout.addStretch()
        size_layout.addWidget(size_label)
        layout.addWidget(size_row)

        # ── בחירת ערכת נושא ──
        theme_title = QLabel("ערכת נושא:")
        theme_title.setFont(QFont("David", 13))
        theme_title.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(theme_title)

        theme_container = QHBoxLayout()
        theme_container.setSpacing(20)

        self.theme_group = QButtonGroup(self)

        # ערכה קלאסית
        classic_box = QVBoxLayout()
        self.radio_classic = QRadioButton("קלאסי")
        self.radio_classic.setChecked(current_theme == 'classic')
        self.theme_group.addButton(self.radio_classic)
        
        self.img_classic = QLabel()
        self.img_classic.setFixedSize(180, 110)
        self.img_classic.setStyleSheet("border: 2px solid #CBD5E0; background: #E1E8ED; border-radius: 4px;")
        self._set_placeholder_image(self.img_classic, "classic_preview.png", "תצוגה קלאסית")
        
        classic_box.addWidget(self.img_classic)
        classic_box.addWidget(self.radio_classic, 0, Qt.AlignmentFlag.AlignCenter)
        theme_container.addLayout(classic_box)

        # ערכה צבעונית
        colorful_box = QVBoxLayout()
        self.radio_colorful = QRadioButton("צבעוני")
        self.radio_colorful.setChecked(current_theme == 'colorful')
        self.theme_group.addButton(self.radio_colorful)
        
        self.img_colorful = QLabel()
        self.img_colorful.setFixedSize(180, 110)
        self.img_colorful.setStyleSheet("border: 2px solid #CBD5E0; background: #2B1A0F; border-radius: 4px;")
        self._set_placeholder_image(self.img_colorful, "colorful_preview.png", "תצוגה צבעונית")
        
        colorful_box.addWidget(self.img_colorful)
        colorful_box.addWidget(self.radio_colorful, 0, Qt.AlignmentFlag.AlignCenter)
        theme_container.addLayout(colorful_box)

        layout.addLayout(theme_container)

        # ── תצוגה מקדימה ──
        preview_lbl = QLabel("תצוגה מקדימה של גופן:")
        preview_lbl.setFont(QFont("David", 11))
        preview_lbl.setStyleSheet("color: #718096;")
        preview_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(preview_lbl)

        self.preview = QLabel("אמר ליה שמואל לרב יהודה: שיננא, חטוף ואכול חטוף ואישתי, דעלמא דאזלינן מיניה כהלולא דמי")
        self.preview.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.preview.setWordWrap(True)
        self.preview.setStyleSheet(
            "background:#FFFFFF;border:1px solid #CBD5E0;border-radius:6px;"
            "padding:12px 14px;color:#2D3748;min-height:55px;"
        )
        layout.addWidget(self.preview)

        layout.addSpacing(8)

        # ── כפתורים ──
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)

        cancel_btn = QPushButton("ביטול")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("שמור")
        ok_btn.setObjectName("ok_btn")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self._on_ok)
        ok_btn.setDefault(True)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        layout.addWidget(btn_row)

        self._update_preview()

    def _set_placeholder_image(self, label: QLabel, filename: str, text: str):
        """מנסה לטעון תמונה, אם לא קיים מציג טקסט זמני."""
        # נתיב יחסי לתיקיית התוכנה
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "assets", filename)
        
        if os.path.exists(path):
            pixmap = QPixmap(path)
            label.setPixmap(pixmap.scaled(label.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
        else:
            label.setText(text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(QFont("David", 12))
            label.setStyleSheet(label.styleSheet() + "color: #718096;")

    def _clamp_size(self, val: int) -> int:
        return max(8, min(36, val))

    def _increase_size(self):
        self._font_size = self._clamp_size(self._font_size + 1)
        self.size_edit.blockSignals(True)
        self.size_edit.setText(str(self._font_size))
        self.size_edit.blockSignals(False)
        self._update_preview()

    def _decrease_size(self):
        self._font_size = self._clamp_size(self._font_size - 1)
        self.size_edit.blockSignals(True)
        self.size_edit.setText(str(self._font_size))
        self.size_edit.blockSignals(False)
        self._update_preview()

    def _on_size_text_changed(self, text: str):
        try:
            val = int(text)
            self._font_size = self._clamp_size(val)
            self._update_preview()
        except ValueError:
            pass

    def _update_preview(self):
        family = self.font_combo.currentText()
        size = self._font_size
        self.preview.setFont(QFont(family, size))
        self.preview.setStyleSheet(
            f"background:#FFFFFF;border:1px solid #CBD5E0;border-radius:6px;"
            f"padding:12px 14px;color:#2D3748;min-height:55px;"
            f"font-family:'{family}';font-size:{size}pt;"
        )

    def _on_ok(self):
        family = self.font_combo.currentText()
        try:
            val = int(self.size_edit.text())
            self._font_size = self._clamp_size(val)
        except ValueError:
            pass
        
        theme = 'colorful' if self.radio_colorful.isChecked() else 'classic'
        self.settings_changed.emit(family, self._font_size, theme)
        self.accept()

    def get_values(self):
        theme = 'colorful' if self.radio_colorful.isChecked() else 'classic'
        return self.font_combo.currentText(), self._font_size, theme
