from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect

THEMES = {
    "VOID": {
        "bg": "#0a0b0d",
        "surface": "#121418",
        "surface2": "#1a1d22",
        "surface3": "#22262c",
        "border": "#2a2e35",
        "text": "#f5f7fa",
        "muted": "#9aa1ab",
        "accent": "#8b7cff",
        "accent2": "#a69bff",
    },
    "ICE": {
        "bg": "#081016",
        "surface": "#0f171e",
        "surface2": "#16212a",
        "surface3": "#1f2b35",
        "border": "#2b3a45",
        "text": "#f1f8fc",
        "muted": "#92a7b5",
        "accent": "#59c7ff",
        "accent2": "#85d8ff",
    },
    "MIDNIGHT": {
        "bg": "#090b12",
        "surface": "#121624",
        "surface2": "#1a2031",
        "surface3": "#232a3f",
        "border": "#2b3550",
        "text": "#f4f6ff",
        "muted": "#929bb1",
        "accent": "#6f92ff",
        "accent2": "#90abff",
    },
    "EMBER": {
        "bg": "#100b0a",
        "surface": "#181210",
        "surface2": "#221916",
        "surface3": "#2d211d",
        "border": "#4a342b",
        "text": "#fff7f1",
        "muted": "#b5a096",
        "accent": "#ff8a5b",
        "accent2": "#ffac87",
    },
}


def stylesheet(name):
    t = THEMES.get(name, THEMES["VOID"])
    return f"""
    QWidget {{
        background: {t['bg']};
        color: {t['text']};
        font-family: 'Segoe UI';
        font-size: 13px;
    }}
    QMainWindow {{ background: {t['bg']}; }}
    QToolTip {{
        background: {t['surface2']};
        color: {t['text']};
        border: 1px solid {t['border']};
        padding: 6px;
    }}
    QFrame#chromeBar {{
        background: {t['surface']};
        border: 1px solid {t['border']};
        border-radius: 16px;
    }}
    QFrame#searchShell {{
        background: {t['surface']};
        border: 1px solid {t['border']};
        border-radius: 20px;
    }}
    QFrame#searchShell:focus-within {{
        border: 1px solid {t['accent']};
    }}
    QLineEdit {{
        background: transparent;
        border: none;
        color: {t['text']};
        padding: 14px 16px;
        font-size: 15px;
    }}
    QLineEdit:focus {{ outline: none; }}
    QPushButton {{
        background: transparent;
        color: {t['text']};
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 8px 11px;
    }}
    QPushButton:hover {{
        background: {t['surface2']};
        border-color: {t['border']};
    }}
    QPushButton[accent="true"] {{
        background: {t['accent']};
        color: white;
        border-color: {t['accent']};
        font-weight: 700;
    }}
    QPushButton[accent="true"]:hover {{
        background: {t['accent2']};
        border-color: {t['accent2']};
    }}
    QTabWidget::pane {{ border: none; background: {t['bg']}; }}
    QTabBar {{ background: transparent; }}
    QTabBar::tab {{
        background: {t['surface']};
        color: {t['muted']};
        border: 1px solid transparent;
        padding: 9px 15px;
        margin-right: 4px;
        border-radius: 10px;
    }}
    QTabBar::tab:selected {{
        color: {t['text']};
        background: {t['surface2']};
        border-color: {t['border']};
    }}
    QTabBar::close-button {{ margin-left: 6px; }}
    QLabel#brand {{
        font-size: 24px;
        font-weight: 900;
        letter-spacing: 3px;
        color: {t['text']};
    }}
    QLabel#searchBrand {{
        font-size: 50px;
        font-weight: 800;
        letter-spacing: 7px;
        color: {t['text']};
    }}
    QLabel#pageTitle {{
        font-size: 30px;
        font-weight: 800;
    }}
    QLabel#muted {{ color: {t['muted']}; }}
    QLabel#chip {{
        color: {t['muted']};
        background: {t['surface2']};
        border: 1px solid {t['border']};
        border-radius: 9px;
        padding: 5px 8px;
    }}
    QComboBox {{
        background: {t['surface']};
        color: {t['text']};
        border: 1px solid {t['border']};
        border-radius: 10px;
        padding: 7px 10px;
    }}
    QComboBox QAbstractItemView {{
        background: {t['surface']};
        color: {t['text']};
        selection-background-color: {t['accent']};
    }}
    QListWidget {{
        background: {t['surface']};
        border: 1px solid {t['border']};
        border-radius: 14px;
        padding: 6px;
    }}
    QListWidget::item {{
        padding: 10px;
        border-radius: 8px;
    }}
    QListWidget::item:hover {{ background: {t['surface2']}; }}
    """


def fade_in(widget, duration=170):
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    widget._orbit_fade = anim
