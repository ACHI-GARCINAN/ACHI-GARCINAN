"""
ערכות נושא לאפליקציה - קלאסי וצבעוני
"""

# ── ערכת נושא קלאסית (v11) ──────────────────────────────────
STYLE_CLASSIC = """
QMainWindow, QWidget {
    background-color: #F0F4F7;
    font-family: 'David', 'Arial', sans-serif;
}
QListWidget#page_list {
    background-color: #E1E8ED;
    border: none;
    color: #4A5568;
    outline: none;
    padding: 6px 0;
}
QListWidget#page_list::item {
    padding: 9px 6px;
    text-align: center;
    border-bottom: 1px solid #D1D9E0;
    font-size: 15px;
}
QListWidget#page_list::item:selected {
    background-color: #B0C4DE;
    color: #2D3748;
    font-weight: bold;
}
QListWidget#page_list::item:hover:!selected {
    background-color: #DDE4E9;
}
QListWidget#masechet_list {
    background-color: #D9E1E8;
    border: none;
    color: #4A5568;
    outline: none;
    padding: 6px 0;
}
QListWidget#masechet_list::item {
    padding: 9px 6px;
    text-align: center;
    border-bottom: 1px solid #CBD5E0;
    font-size: 14px;
}
QListWidget#masechet_list::item:selected {
    background-color: #A0B4CC;
    color: #2D3748;
    font-weight: bold;
}
QListWidget#masechet_list::item:hover:!selected {
    background-color: #CFD9E1;
}
QScrollBar:vertical {
    background: #EBF0F5; width: 7px; border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #A0B4CC; border-radius: 3px; min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QSplitter::handle { background-color: #CBD5E0; }
QCheckBox {
    color: #4A5568;
    font-size: 12px;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border-radius: 3px;
    border: 1px solid #A0B4CC;
    background: #F0F4F7;
}
QCheckBox::indicator:checked {
    background: #A0B4CC;
    border: 1px solid #718096;
}
"""

WITNESS_COLORS_CLASSIC = [
    ("#5A6A82", "#E8EEF4"),
    ("#5A6A82", "#E8EEF4"),
    ("#5A6A82", "#E8EEF4"),
    ("#5A6A82", "#E8EEF4"),
    ("#5A6A82", "#E8EEF4"),
    ("#5A6A82", "#E8EEF4"),
    ("#5A6A82", "#E8EEF4"),
    ("#5A6A82", "#E8EEF4"),
]

# ── ערכת נושא צבעונית (v8_fixed) ──────────────────────────────
STYLE_COLORFUL = """
QMainWindow, QWidget {
    background-color: #F7F3EC;
    font-family: 'David', 'Arial', sans-serif;
}
QListWidget#page_list {
    background-color: #2B1A0F;
    border: none;
    color: #C8A87A;
    outline: none;
    padding: 6px 0;
}
QListWidget#page_list::item {
    padding: 9px 6px;
    text-align: center;
    border-bottom: 1px solid #3A2418;
    font-size: 15px;
}
QListWidget#page_list::item:selected {
    background-color: #7A3810;
    color: #FFF5E6;
    font-weight: bold;
}
QListWidget#page_list::item:hover:!selected {
    background-color: #3A2418;
}
QListWidget#masechet_list {
    background-color: #1A2B1A;
    border: none;
    color: #A8C87A;
    outline: none;
    padding: 6px 0;
}
QListWidget#masechet_list::item {
    padding: 9px 6px;
    text-align: center;
    border-bottom: 1px solid #243424;
    font-size: 14px;
}
QListWidget#masechet_list::item:selected {
    background-color: #2E6010;
    color: #F0FFE6;
    font-weight: bold;
}
QListWidget#masechet_list::item:hover:!selected {
    background-color: #243424;
}
QScrollBar:vertical {
    background: #EDE8DF; width: 7px; border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #C0A87A; border-radius: 3px; min-height: 24px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QSplitter::handle { background-color: #D5C8B0; }
QCheckBox {
    color: #F0DFC0;
    font-size: 12px;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 15px;
    height: 15px;
    border-radius: 3px;
    border: 1px solid #C8A060;
    background: #2B1A0F;
}
QCheckBox::indicator:checked {
    background: #C8A060;
    border: 1px solid #E8C080;
}
"""

WITNESS_COLORS_COLORFUL = [
    ("#5B3A8A", "#F0ECF8"),
    ("#1A5E8A", "#EAF3FA"),
    ("#2E7A4A", "#E8F5EE"),
    ("#8A4A1A", "#FBF0E8"),
    ("#7A1A3A", "#F8EAF0"),
    ("#2A6A6A", "#E8F5F5"),
    ("#5A6A1A", "#F2F5E8"),
    ("#6A2A6A", "#F5E8F5"),
]

# ברירת מחדל
STYLE = STYLE_CLASSIC
WITNESS_COLORS = WITNESS_COLORS_CLASSIC

def get_theme_styles(theme_name: str):
    if theme_name == 'colorful':
        return STYLE_COLORFUL, WITNESS_COLORS_COLORFUL
    return STYLE_CLASSIC, WITNESS_COLORS_CLASSIC

def get_theme_config(theme_name: str):
    if theme_name == 'colorful':
        return {
            'main_bg': '#F7F3EC',
            'header_bg': '#2B1A0F',
            'header_text': '#FFF5E6',
            'header_subtext': '#C8A87A',
            'btn_color': '#C8A060',
            'btn_border': '#7A5030',
            'btn_hover_bg': '#3A2418',
            'btn_text_hover': '#FFF5E6',
            'search_bg': '#3A2418',
            'search_text': '#FFF5E6',
            'search_border': '#6A4020',
            'search_placeholder': '#806040',
            'section_tag_bg': '#F2E8D8',
            'section_tag_text': '#8B4513',
            'section_text': '#1A0800',
            'section_normal_bg': '#FFFDF8',
            'section_normal_border': '#E0D8C8',
            'section_hover_bg': '#FFF5E6',
            'section_hover_border': '#C8A060',
            'section_hover_right': '#8B4513',
            'section_selected_bg': '#FFF0DC',
            'section_selected_border': '#8B4513',
            'section_selected_right': '#5A1A00',
            'section_diff_bg': '#FFF8F0',
            'section_diff_border': '#FF6B35',
            'section_diff_right': '#CC3300',
            'word_normal_text': '#1A0800',
            'word_hover_bg': '#FFF0C0',
            'word_hover_text': '#5A1A00',
            'word_selected_bg': '#FFD080',
            'word_selected_text': '#3A0A00',
            'word_missing_text': '#C0A080',
            'panel_header_bg': '#2B1A0F',
            'panel_header_text': '#FFF5E6',
            'panel_header_border': '#7A5030',
            'panel_hint_text': '#C8A87A',
        }
    else:
        return {
            'main_bg': '#F0F4F7',
            'header_bg': '#E1E8ED',
            'header_text': '#2D3748',
            'header_subtext': '#718096',
            'btn_color': '#5A6A82',
            'btn_border': '#A0B4CC',
            'btn_hover_bg': '#DDE4E9',
            'btn_text_hover': '#2D3748',
            'search_bg': '#F0F4F7',
            'search_text': '#2D3748',
            'search_border': '#CBD5E0',
            'search_placeholder': '#A0AEC0',
            'section_tag_bg': '#E2E8F0',
            'section_tag_text': '#4A5568',
            'section_text': '#2D3748',
            'section_normal_bg': '#FFFFFF',
            'section_normal_border': '#CBD5E0',
            'section_hover_bg': '#F7FAFC',
            'section_hover_border': '#A0B4CC',
            'section_hover_right': '#5A6A82',
            'section_selected_bg': '#EDF2F7',
            'section_selected_border': '#5A6A82',
            'section_selected_right': '#2D3748',
            'section_diff_bg': '#FFF5F5',
            'section_diff_border': '#FC8181',
            'section_diff_right': '#E53E3E',
            'word_normal_text': '#2D3748',
            'word_hover_bg': '#E2E8F0',
            'word_hover_text': '#1A202C',
            'word_selected_bg': '#B0C4DE',
            'word_selected_text': '#1A202C',
            'word_missing_text': '#A0AEC0',
            'panel_header_bg': '#E1E8ED',
            'panel_header_text': '#2D3748',
            'panel_header_border': '#A0B4CC',
            'panel_hint_text': '#718096',
        }