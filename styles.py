STYLE = """
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

WITNESS_COLORS = [
    ("#5B3A8A", "#F0ECF8"),
    ("#1A5E8A", "#EAF3FA"),
    ("#2E7A4A", "#E8F5EE"),
    ("#8A4A1A", "#FBF0E8"),
    ("#7A1A3A", "#F8EAF0"),
    ("#2A6A6A", "#E8F5F5"),
    ("#5A6A1A", "#F2F5E8"),
    ("#6A2A6A", "#F5E8F5"),
]
