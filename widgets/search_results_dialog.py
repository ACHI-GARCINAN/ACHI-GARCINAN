import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from .search_spinner import SearchSpinner
from db import search_word_in_shas


class SearchWorker(QThread):
    finished = pyqtSignal(list)

    def __init__(self, word: str):
        super().__init__()
        self._word = word

    def run(self):
        results = search_word_in_shas(self._word)
        self.finished.emit(results)


class SearchResultsDialog(QDialog):
    def __init__(self, word: str, theme: str = 'classic', parent=None):
        super().__init__(parent)
        self._word = word
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setWindowTitle(f'חיפוש: {word}')
        from main_window import get_icon
        self.setWindowIcon(get_icon())
        self.setMinimumSize(420, 380)

        is_colorful = (theme == 'colorful')
        bg       = '#F7F3EC' if is_colorful else '#F0F4F7'
        text     = '#1A0800' if is_colorful else '#2D3748'
        accent   = '#C8A060' if is_colorful else '#5A6A82'
        item_sel = '#FFF0DC' if is_colorful else '#EDF2F7'
        border   = '#D5C8A0' if is_colorful else '#CBD5E0'

        self.setStyleSheet(f"QDialog{{background:{bg};}}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel(f'תוצאות חיפוש עבור: {word}')
        title.setFont(QFont('David', 13, QFont.Weight.Bold))
        title.setStyleSheet(f'color:{text};background:transparent;')
        layout.addWidget(title)

        self.count_label = QLabel('מחפש...')
        self.count_label.setFont(QFont('David', 11))
        self.count_label.setStyleSheet(f'color:{accent};background:transparent;')
        layout.addWidget(self.count_label)

        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont('David', 12))
        self.list_widget.setStyleSheet(f"""
            QListWidget{{background:{bg};border:1px solid {border};border-radius:8px;outline:none;}}
            QListWidget::item{{padding:8px 12px;border-bottom:1px solid {border};color:{text};}}
            QListWidget::item:selected{{background:{accent};color:white;font-weight:bold;border-right:4px solid {accent};}}
            QListWidget::item:hover:!selected{{background:{accent}20;}}
        """)
        layout.addWidget(self.list_widget, 1)

        btn_row = QHBoxLayout()

        self.copy_btn = QPushButton('העתק מיקום')
        self.copy_btn.setFont(QFont('David', 11))
        self.copy_btn.setFixedHeight(32)
        self.copy_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.copy_btn.setEnabled(False)
        self.copy_btn.setStyleSheet(f"""
            QPushButton{{background:{accent};color:white;border:none;
            border-radius:6px;padding:0 16px;}}
            QPushButton:disabled{{background:{accent}60;}}
        """)
        self.copy_btn.clicked.connect(self._copy_location)
        btn_row.addWidget(self.copy_btn)

        close_btn = QPushButton('סגור')
        close_btn.setFont(QFont('David', 11))
        close_btn.setFixedHeight(32)
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.setStyleSheet(f"""
            QPushButton{{background:transparent;color:{text};
            border:1px solid {border};border-radius:6px;padding:0 16px;}}
            QPushButton:hover{{border-color:{accent};}}
        """)
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        self.list_widget.itemSelectionChanged.connect(
            lambda: self.copy_btn.setEnabled(len(self.list_widget.selectedItems()) > 0)
        )

        self._spinner = SearchSpinner(self)
        self._spinner.show()

        self._worker = SearchWorker(word)
        self._worker.finished.connect(self._load_results)
        self._worker.start()

    def _load_results(self, results: list):
        if not results:
            self.count_label.setText('לא נמצאו תוצאות')
            self._spinner.hide()
            return

        self.count_label.setText(f'נמצאו {len(results)} תוצאות')

        for r in results:
            ms_clean = r['masechet'].replace('מסכת ', '').strip()
            display = f"{ms_clean}  ·  דף {r['page']}  ·  {r['section']}"
            copy_text = f"{ms_clean} דף {r['page']}"

            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, copy_text)
            self.list_widget.addItem(item)

        self._spinner.hide()

    def _copy_location(self):
        items = self.list_widget.selectedItems()
        if not items:
            return
        text = items[0].data(Qt.ItemDataRole.UserRole)
        QApplication.clipboard().setText(text)
        self.copy_btn.setText('✓ הועתק')
        QTimer.singleShot(1500, lambda: self.copy_btn.setText('העתק מיקום'))