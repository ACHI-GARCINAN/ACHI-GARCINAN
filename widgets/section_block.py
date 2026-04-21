from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor

from utils import build_vilna_diff_html
from styles import get_theme_config


class SectionBlock(QFrame):
    clicked = pyqtSignal()

    def __init__(self, section: dict, main_witness: str,
                 font_family: str = 'David', font_size: int = 16, theme: str = 'classic', parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.section = section
        self.main_witness = main_witness
        self.is_selected = False
        self._active_diff_witness = None
        self._plain_text = ''
        self._text_lbl = None
        self._font_family = font_family
        self._font_size = font_size
        self._theme = theme
        self._has_search_match = False

        self.setObjectName("section_block")
        self._update_styles()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 10, 16, 12)
        self._layout.setSpacing(6)

        self.tag = QLabel(section['section'])
        self.tag.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.tag.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.tag.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._layout.addWidget(self.tag, alignment=Qt.AlignmentFlag.AlignRight)

        text = section['witnesses'].get(main_witness, '') or ''
        if text == 'None':
            text = ''
        self._plain_text = text

        self._text_lbl = QLabel()
        self._text_lbl.setWordWrap(True)
        self._text_lbl.setFont(QFont(font_family, font_size))
        self._text_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self._text_lbl.setTextFormat(Qt.TextFormat.RichText)
        self._layout.addWidget(self._text_lbl)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
        self._update_ui_colors()

    def _update_styles(self):
        cfg = get_theme_config(self._theme)
        self._normal_style   = f"QFrame#section_block{{background-color:{cfg['section_normal_bg']};border:1px solid {cfg['section_normal_border']};border-radius:8px;margin:3px 8px;}}"
        self._hover_style    = f"QFrame#section_block{{background-color:{cfg['section_hover_bg']};border:1px solid {cfg['section_hover_border']};border-right:4px solid {cfg['section_hover_right']};border-radius:8px;margin:3px 8px;}}"
        self._selected_style = f"QFrame#section_block{{background-color:{cfg['section_selected_bg']};border:1px solid {cfg['section_selected_border']};border-right:4px solid {cfg['section_selected_right']};border-radius:8px;margin:3px 8px;}}"
        self._diff_style     = f"QFrame#section_block{{background-color:{cfg['section_diff_bg']};border:1px solid {cfg['section_diff_border']};border-right:4px solid {cfg['section_diff_right']};border-radius:8px;margin:3px 8px;}}"
        
        if self._active_diff_witness:
            self.setStyleSheet(self._diff_style)
        elif self.is_selected:
            self.setStyleSheet(self._selected_style)
        else:
            self.setStyleSheet(self._normal_style)

    def _update_ui_colors(self):
        cfg = get_theme_config(self._theme)
        self.tag.setStyleSheet(f"color:{cfg['section_tag_text']};background-color:{cfg['section_tag_bg']};border-radius:4px;padding:2px 8px;")
        self._text_lbl.setText(self._make_justified_html(self._plain_text if self._plain_text else '(אין טקסט)'))

    def _make_justified_html(self, text: str) -> str:
        cfg = get_theme_config(self._theme)
        return (
            f'<div dir="rtl" style="font-family:{self._font_family},serif;'
            f'font-size:{self._font_size}pt;color:{cfg["section_text"]};text-align:justify;">'
            f'{text}</div>'
        )

    def update_font(self, font_family: str, font_size: int, theme: str = None):
        self._font_family = font_family
        self._font_size = font_size
        if theme:
            self._theme = theme
            self._update_styles()
        
        self._text_lbl.setFont(QFont(font_family, font_size))
        if self._active_diff_witness:
            w_name = self._active_diff_witness
            self._active_diff_witness = None
            self.show_witness_diff(w_name)
        else:
            self._update_ui_colors()

    def show_witness_diff(self, witness_name: str):
        if self._active_diff_witness == witness_name:
            self._active_diff_witness = None
            self._update_ui_colors()
            self.setStyleSheet(self._selected_style if self.is_selected else self._normal_style)
            return

        self._active_diff_witness = witness_name
        witness_text = self.section['witnesses'].get(witness_name, '') or ''
        if witness_text == 'None':
            witness_text = ''

        if self._plain_text and witness_text:
            html = build_vilna_diff_html(self._plain_text, witness_text)
            self._text_lbl.setTextFormat(Qt.TextFormat.RichText)
            cfg = get_theme_config(self._theme)
            self._text_lbl.setText(
                f'<div dir="rtl" style="font-family:{self._font_family},serif;'
                f'font-size:{self._font_size}pt;color:{cfg["section_text"]};text-align:justify;">{html}</div>'
            )
        self.setStyleSheet(self._diff_style)

    def clear_diff(self):
        self._active_diff_witness = None
        self._update_ui_colors()
        self.setStyleSheet(self._selected_style if self.is_selected else self._normal_style)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        if self._active_diff_witness:
            self.setStyleSheet(self._diff_style)
        else:
            self.setStyleSheet(self._selected_style if selected else self._normal_style)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def search_highlight(self, term: str) -> bool:
        import html as _html
        if not self._plain_text or not term:
            self._has_search_match = False
            self._update_ui_colors()
            return False

        escaped_term = _html.escape(term)
        if term in self._plain_text:
            highlighted = _html.escape(self._plain_text).replace(
                escaped_term,
                f'<span style="background-color: yellow; color: black;">{escaped_term}</span>'
            )
            self._text_lbl.setTextFormat(Qt.TextFormat.RichText)
            self._text_lbl.setText(self._make_justified_html(highlighted))
            self._has_search_match = True
            return True
        else:
            self._has_search_match = False
            self._update_ui_colors()
            return False

        escaped_term = _html.escape(term)
        if term in self._plain_text:
            highlighted = _html.escape(self._plain_text).replace(
                escaped_term,
                f'<span style="background-color: yellow; color: black;">{escaped_term}</span>'
            )
            self._text_lbl.setTextFormat(Qt.TextFormat.RichText)
            self._text_lbl.setText(self._make_justified_html(highlighted))
            self._has_search_match = True
            return True
        else:
            self._has_search_match = False
            self._update_ui_colors()
            return False

    def has_search_match(self) -> bool:
        return self._has_search_match

    def enterEvent(self, event):
        if not self.is_selected and not self._active_diff_witness:
            self.setStyleSheet(self._hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_selected and not self._active_diff_witness:
            self.setStyleSheet(self._normal_style)
        elif self._active_diff_witness:
            self.setStyleSheet(self._diff_style)
        super().leaveEvent(event)
