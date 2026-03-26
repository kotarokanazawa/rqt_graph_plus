APP_STYLE = """
QWidget {
    background-color: #0b1020;
    color: #dbe7ff;
    font-family: "Noto Sans CJK JP", "Yu Gothic UI", "Ubuntu", sans-serif;
    font-size: 14pt;
}
QFrame#topBar {
    background-color: rgba(18, 28, 48, 232);
    border: 1px solid #243a63;
    border-radius: 12px;
}
QPushButton {
    background-color: #15233d;
    border: 1px solid #2e4c80;
    border-radius: 8px;
    padding: 6px 11px;
    color: #e5eeff;
}
QPushButton:hover { background-color: #1b2f52; }
QPushButton:pressed { background-color: #11203a; }
QLineEdit {
    background-color: #0e1a30;
    border: 1px solid #29446d;
    border-radius: 8px;
    padding: 6px 9px;
    color: #e5eeff;
}
QCheckBox { spacing: 6px; color: #dbe7ff; font-size: 13pt; }
QCheckBox::indicator { width: 17px; height: 17px; }
QCheckBox::indicator:unchecked {
    border: 1px solid #355888; background: #0d1730; border-radius: 4px;
}
QCheckBox::indicator:checked {
    border: 1px solid #4aa3ff; background: #1d4ed8; border-radius: 4px;
}
QLabel#titleLabel { font-size: 13pt; font-weight: bold; color: #f2f7ff; }
QLabel#subLabel { color: #89a6d8; font-size: 12pt; }
QFrame#sidePanel {
    background-color: rgba(14, 22, 39, 235);
    border: 1px solid #21365c;
    border-radius: 14px;
}
QTextEdit {
    background-color: #0c1628;
    border: 1px solid #29446d;
    border-radius: 10px;
    color: #dbe7ff;
    padding: 8px;
    font-size: 13pt;
}
QGraphicsView {
    background-color: #070c17;
    border: 1px solid #22375b;
    border-radius: 14px;
}
"""
