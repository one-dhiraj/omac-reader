from PySide6.QtWidgets import QToolTip
from PySide6.QtCore import Qt

APP_STYLESHEET = """
/* ---- Global foundation ---- */

QWidget {
    color: #0f172a;                 /* High-contrast Slate Dark text */
    font-family: "Inter", "Segoe UI", "Noto Sans", sans-serif;
    font-size: 11pt;                /* Increased base scale for better readability */
}

QMainWindow, QWidget#centralwidget, QStackedWidget {
    background-color: #f1f5f9;       /* Bright, distinct modern gray background canvas */
}

/* ---- Tooltips ---- */

QToolTip {
    background-color: #ffffff;       /* Pure white elegant card background */
    color: #1e293b;                 /* High-contrast slate dark typography */
    border: 1px solid #cbd5e1;      /* Crisp, subtle boundary edge line */
    border-radius: 5px;             /* Target rounded corners style */
    padding: 4px 10px;              /* Slim, highly scannable inner layout padding */
    font-size: 10pt;                /* Increased slightly to stay proportional */
}


/* ---- Toolbars ---- */

QToolBar {
    background-color: #ffffff;       /* Pure white bar card */
    border: none;
    border-bottom: 1px solid #cbd5e1;
    spacing: 6px;
    padding: 5px 10px;
}

QToolBar::separator {
    background-color: #cbd5e1;
    width: 1px;
    margin: 6px 8px;
}

QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 8px;
}

QToolButton:hover {
    background-color: #f1f5f9;
}

QToolButton:pressed,
QToolButton:checked {
    background-color: #dbeafe;       /* Vibrant soft royal blue background tint */
    color: #1d4ed8;                  /* Strong royal blue accent text */
}

QToolButton:disabled {
    color: #94a3b8;
}

/* ---- Toolbar Custom Close Button ---- */

QToolButton#toolbar_close_button {
    font-size: 12pt;                 /* Bumped up to match application balance */
    font-weight: bold;
    color: #64748b;                  /* Matches your existing muted gray text */
    padding: 5px 12px;               /* Slightly wider padding for a balanced button look */
    border-radius: 4px;
}

QToolButton#toolbar_close_button:hover {
    background-color: #fee2e2;       /* Pastel light red background */
    color: #ef4444;                  /* Crisp bright red cross */
}

QToolButton#toolbar_close_button:pressed {
    background-color: #fca5a5;       /* Slightly deeper red when pressed */
    color: #991b1b;
}

/* ---- Buttons ---- */

QPushButton {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #f8fafc;
    border-color: #94a3b8;
}

QPushButton:pressed {
    background-color: #e2e8f0;
    border-color: #64748b;
}

QPushButton:disabled {
    background-color: #f1f5f9;
    color: #94a3b8;
    border-color: #e2e8f0;
}

/* ---- Reading and editor surfaces ---- */

QListWidget {
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    outline: none;
    padding: 4px;
}

QListWidget::item {
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 10px;
    margin: 2px 4px;
}

QListWidget::item:hover {
    background-color: #f1f5f9;
}

QListWidget::item:selected {
    background-color: #2563eb;       /* Vibrant blue highlight selection */
    color: #ffffff;
}

/* ---- Labels ---- */

QLabel {
    background: transparent;
}

QLabel#page_info_label {
    color: #475569;
    font-size: 10pt;                /* Scaled up from 9pt */
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* ---- Input controls ---- */

QLineEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #bfdbfe;
    selection-color: #1e3a8a;
}

QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {
    border: 1px solid #2563eb;       /* Clean royal blue focus ring */
}

/* Modernise QComboBox dropdown arrow menus */
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: none;
}

QComboBox::down-arrow {
    image: none;
    border: 4px solid transparent;
    border-top-color: #475569;       /* Modern minimalist chevron hook */
    margin-top: 4px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QCheckBox,
QRadioButton {
    spacing: 8px;
}

/* ---- Scrollbars ---- */

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 4px 2px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    margin: 2px 4px;
}

QScrollBar::handle:vertical,
QScrollBar::handle:horizontal {
    background: #cbd5e1;
    border-radius: 4px;
    min-height: 24px;
    min-width: 24px;
}

QScrollBar::handle:vertical:hover,
QScrollBar::handle:horizontal:hover {
    background: #94a3b8;
}

QScrollBar::add-line,
QScrollBar::sub-line {
    width: 0;
    height: 0;
}

QScrollBar::add-page,
QScrollBar::sub-page {
    background: transparent;
}

/* ---- Status bar ---- */

QStatusBar {
    background-color: #ffffff;
    color: #475569;
    border-top: 1px solid #cbd5e1;
    padding: 4px 8px;
}

QStatusBar::item {
    border: none;
}

/* ---- Progress and dialogs ---- */

QProgressDialog {
    min-width: 450px;
}

/* ---- Progress Bar Fix ---- */

QProgressBar {
    background-color: #e2e8f0;
    border: none;
    border-radius: 4px;
    height: 16px;                   /* Increased slightly to fit the 11pt font cleanly */
    text-align: right;              /* Aligns the percentage cleanly on the right */
    margin-right: 44px;             /* Expanded safe-zone gap for larger text */
}

QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 4px;
}

QMessageBox,
QProgressDialog,
QFileDialog {
    background-color: #ffffff;
}
"""

def apply_app_style(app):
    """Apply the shared visual theme to the application."""
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)
    
    QToolTip.setFont(app.font())  # Instantiates the underlying widget cache safe layer
    for widget in app.allWidgets():
        if widget.inherits("QToolTip"):
            widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            # Removes default Windows/OS native shadow artifacting that forces sharp corners
            widget.setWindowFlags(widget.windowFlags() | Qt.WindowType.FramelessWindowHint)
