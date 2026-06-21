"""
icons.py — אייקונים SVG מותאמים לתוכנת "נוסחאות התלמוד"
=========================================================
שימוש:
    from icons import get_icon_pixmap, IconName

    btn.setIcon(get_icon_pixmap(IconName.SETTINGS, color="#C8A060", size=22))

הצבע מועבר מחוץ, כך שהאייקון עובד בשתי ערכות הנושא —
בערכת הנושא הקלאסית העבירו "#5A6A82", בצבעונית "#C8A060".

אפשרות 2: שימוש ב-svg_str ישירות עם QSvgRenderer.
"""

from __future__ import annotations
import os
from enum import Enum, auto

from PyQt6.QtCore import QByteArray, QSize, Qt
from PyQt6.QtGui import QPixmap, QPainter, QIcon
from PyQt6.QtSvg import QSvgRenderer


class IconName(Enum):
    INFO        = auto()   # כפתור מידע/זכויות
    SETTINGS    = auto()   # הגדרות (גלגל שיניים)
    OPTIONS     = auto()   # אפשרויות תצוגה (סליידרים)
    NAV_PREV    = auto()   # ניווט לדף הקודם (RTL: חץ ימינה)
    NAV_NEXT    = auto()   # ניווט לדף הבא  (RTL: חץ שמאלה)
    SIDEBAR_SHOW = auto()  # הצג סרגל צד (חץ ימינה + פס)
    SIDEBAR_HIDE = auto()  # הסתר סרגל צד (חץ שמאלה + פס)
    MODE_SECTIONS = auto() # תצוגת קטעים (מסמך)
    MODE_WORDS    = auto() # תצוגת מילים (בלוקי מילים)
    MANUSCRIPT    = auto() # מידע כתב יד (מגילה)
    SEARCH        = auto() # חיפוש (זכוכית מגדלת)
    COPY          = auto() # העתק
    CHECK         = auto() # אישור/הועתק (וי)
    CLOSE         = auto() # סגור (X)


# ─── תבניות SVG ────────────────────────────────────────────────
# {color} מוחלף ב-get_icon_pixmap. הסמלים מוכנסים ב-viewBox 24×24.

_TEMPLATES: dict[IconName, str] = {

    IconName.INFO: """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <circle cx="12" cy="5" r="2" fill="{color}"/>
  <line x1="12" y1="11" x2="12" y2="19" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>
</svg>""",

    IconName.SETTINGS: """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
  <circle cx="12" cy="12" r="3"/>
</svg>""",

    IconName.OPTIONS: """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <line x1="3" y1="7"  x2="21" y2="7"  stroke="{color}" stroke-width="1.6" stroke-linecap="round"/>
  <line x1="3" y1="12" x2="21" y2="12" stroke="{color}" stroke-width="1.6" stroke-linecap="round"/>
  <line x1="3" y1="17" x2="21" y2="17" stroke="{color}" stroke-width="1.6" stroke-linecap="round"/>
  <circle cx="15" cy="7"  r="2.5" fill="none" stroke="{color}" stroke-width="1.5"/>
  <circle cx="9"  cy="12" r="2.5" fill="none" stroke="{color}" stroke-width="1.5"/>
  <circle cx="17" cy="17" r="2.5" fill="none" stroke="{color}" stroke-width="1.5"/>
</svg>""",

    # RTL: "הקודם" = מעבר לדף ימינה
    IconName.NAV_PREV: """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <path d="M9 6l6 6-6 6" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",

    # RTL: "הבא" = מעבר לדף שמאלה
    IconName.NAV_NEXT: """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <path d="M15 6l-6 6 6 6" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",

    IconName.SIDEBAR_SHOW: """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <rect x="17" y="4" width="4" height="16" rx="1.5" fill="{color}" />
  <path d="M12 8l-5 4 5 4" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",

    IconName.SIDEBAR_HIDE: """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <rect x="3" y="4" width="4" height="16" rx="1.5" fill="{color}" />
  <path d="M12 8l5 4-5 4" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",




    IconName.MODE_SECTIONS: """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <!-- קטע עליון: כרטיס עם תגית קטן בפינה ימנית ושורות טקסט -->
  <rect x="2" y="2" width="20" height="8.5" rx="2" stroke="{color}" stroke-width="1.4"/>
  <rect x="15.5" y="2" width="4.5" height="3" rx="1" fill="{color}" opacity="0.55"/>
  <line x1="4" y1="7"  x2="13" y2="7"  stroke="{color}" stroke-width="1.2" stroke-linecap="round"/>
  <line x1="4" y1="9.2" x2="10" y2="9.2" stroke="{color}" stroke-width="1.2" stroke-linecap="round" opacity="0"/>
  <!-- קטע תחתון: כרטיס שני -->
  <rect x="2" y="13" width="20" height="8.5" rx="2" stroke="{color}" stroke-width="1.4"/>
  <rect x="15.5" y="13" width="4.5" height="3" rx="1" fill="{color}" opacity="0.55"/>
  <line x1="4" y1="18"  x2="14" y2="18"  stroke="{color}" stroke-width="1.2" stroke-linecap="round"/>
  <line x1="4" y1="20.2" x2="9" y2="20.2" stroke="{color}" stroke-width="1.2" stroke-linecap="round"/>
</svg>""",

    IconName.MODE_WORDS: """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <!-- שורת מילים 1: שלוש בועות מילה — RTL (גדולה, בינונית, קטנה) -->
  <rect x="15" y="2.5" width="7"   height="3.5" rx="1.5" fill="{color}" opacity="0.85"/>
  <rect x="8"  y="2.5" width="5.5" height="3.5" rx="1.5" fill="{color}" opacity="0.85"/>
  <rect x="2"  y="2.5" width="4.5" height="3.5" rx="1.5" fill="{color}" opacity="0.85"/>
  <!-- שורת מילים 2 -->
  <rect x="17" y="8"  width="5"   height="3.5" rx="1.5" fill="{color}" opacity="0.7"/>
  <rect x="9"  y="8"  width="6.5" height="3.5" rx="1.5" fill="{color}" opacity="0.7"/>
  <rect x="2"  y="8"  width="5.5" height="3.5" rx="1.5" fill="{color}" opacity="0.7"/>
  <!-- שורת מילים 3 -->
  <rect x="16" y="13.5" width="6"   height="3.5" rx="1.5" fill="{color}" opacity="0.55"/>
  <rect x="8"  y="13.5" width="6.5" height="3.5" rx="1.5" fill="{color}" opacity="0.55"/>
  <rect x="2"  y="13.5" width="4.5" height="3.5" rx="1.5" fill="{color}" opacity="0.55"/>
  <!-- שורת מילים 4: חלקית -->
  <rect x="16" y="19" width="6"   height="3.5" rx="1.5" fill="{color}" opacity="0.35"/>
  <rect x="9"  y="19" width="5"   height="3.5" rx="1.5" fill="{color}" opacity="0.35"/>
</svg>""",

    IconName.MANUSCRIPT: """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <path d="M6 3 C3 3 3 6.5 6 6.5 L18 6.5 C21 6.5 21 3 18 3 Z"
        stroke="{color}" stroke-width="1.5" fill="none"/>
  <path d="M6 17.5 C3 17.5 3 21 6 21 L18 21 C21 21 21 17.5 18 17.5 Z"
        stroke="{color}" stroke-width="1.5" fill="none"/>
  <rect x="6" y="6.5" width="12" height="11" stroke="{color}" stroke-width="1.5" fill="none"/>
  <line x1="9" y1="10" x2="15" y2="10" stroke="{color}" stroke-width="1.2" stroke-linecap="round"/>
  <line x1="9" y1="13" x2="15" y2="13" stroke="{color}" stroke-width="1.2" stroke-linecap="round"/>
</svg>""",

    IconName.SEARCH: """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <circle cx="10.5" cy="10.5" r="6.5" stroke="{color}" stroke-width="1.8"/>
  <line x1="15.5" y1="15.5" x2="21" y2="21" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
</svg>""",

    IconName.COPY: """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <rect x="3" y="7"  width="13" height="15" rx="2" stroke="{color}" stroke-width="1.5"/>
  <path d="M8 7V5a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-2"
        stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>
</svg>""",

    IconName.CHECK: """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <path d="M4 13l5 5L20 6" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",

    IconName.CLOSE: """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <line x1="5" y1="5" x2="19" y2="19" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <line x1="19" y1="5" x2="5"  y2="19" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
</svg>""",
}


def get_icon_pixmap(
    name: IconName,
    color: str = "#5A6A82",
    size: int = 20,
    device_pixel_ratio: float = 1.0,
) -> QPixmap:
    """
    מחזיר QPixmap של האייקון בגודל ובצבע הרצויים.

    Parameters
    ----------
    name   : IconName
    color  : צבע hex — כלאסי "#5A6A82", צבעוני "#C8A060"
    size   : גודל בפיקסלים (ריבוע)
    device_pixel_ratio : עבור מסכי HiDPI
    """
    template = _TEMPLATES.get(name, "")
    svg_str = template.replace("{color}", color)
    svg_bytes = QByteArray(svg_str.strip().encode("utf-8"))

    renderer = QSvgRenderer(svg_bytes)
    px_size = int(size * device_pixel_ratio)
    pixmap = QPixmap(px_size, px_size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()

    pixmap.setDevicePixelRatio(device_pixel_ratio)
    return pixmap


def get_icon(
    name: IconName,
    color: str = "#5A6A82",
    size: int = 20,
) -> QIcon:
    """מחזיר QIcon."""
    return QIcon(get_icon_pixmap(name, color, size))


# ── ניחוש אוטומטי של צבע לפי ערכת נושא ──────────────────────

THEME_COLORS = {
    "classic":  "#5A6A82",
    "colorful": "#C8A060",
}


def get_theme_icon(name: IconName, theme: str, size: int = 20) -> QIcon:
    """מחזיר QIcon בצבע המתאים לערכת הנושא."""
    color = THEME_COLORS.get(theme, THEME_COLORS["classic"])
    return get_icon(name, color, size)


def get_app_icon() -> QIcon:
    """מחזיר את אייקון האפליקציה — משמש בכל חלונות התוכנה."""
    from db import get_base_dir
    base = get_base_dir()
    for name in ('icon.ico', 'logo.ico', 'icon.png', 'logo.png'):
        path = os.path.join(base, name)
        if os.path.exists(path):
            return QIcon(path)
    return QIcon()
