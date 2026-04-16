STYLE = """
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

# ערכת צבעים אחידה לעדי הנוסח - גווני כחול-אפור
WITNESS_COLORS = [
    ("#5A6A82", "#E8EEF4"),
    ("#5A6A82", "#E8EEF4"),
    ("#5A6A82", "#E8EEF4"),
    ("#5A6A82", "#E8EEF4"),
    ("#5A6A82", "#E8EEF4"),
    ("#5A6A82", "#E8EEF4"),
    ("#5A6A82", "#E8EEF4"),
    ("#5A6A82", "#E8EEF4"),
]
