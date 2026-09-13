from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect


TRANSLATIONS = {
    "ru": {
        "home": "Главная", "tabs": "Вкладки", "history": "История", "bookmarks": "Закладки",
        "downloads": "Загрузки", "notes": "Заметки", "settings": "Настройки", "search": "Поиск или адрес сайта",
        "quick": "Быстрый доступ", "add": "Добавить", "welcome": "Добро пожаловать в Orbit",
        "future": "B R O W S E   T H E   F U T U R E", "weather": "Погода", "profile": "Профиль",
        "language": "Язык интерфейса", "appearance": "Внешний вид", "behavior": "Поведение",
        "search_engine": "Поисковая система", "site_theming": "Оформлять сайты в стиле Orbit",
        "auto_update": "Автоматические обновления", "animations": "Плавные анимации",
    },
    "en": {
        "home": "Home", "tabs": "Tabs", "history": "History", "bookmarks": "Bookmarks",
        "downloads": "Downloads", "notes": "Notes", "settings": "Settings", "search": "Search or enter address",
        "quick": "Quick access", "add": "Add", "welcome": "Welcome to Orbit",
        "future": "B R O W S E   T H E   F U T U R E", "weather": "Weather", "profile": "Profile",
        "language": "Interface language", "appearance": "Appearance", "behavior": "Behavior",
        "search_engine": "Search engine", "site_theming": "Apply Orbit style to websites",
        "auto_update": "Automatic updates", "animations": "Smooth animations",
    },
}

def tr(language, key):
    return TRANSLATIONS.get(language, TRANSLATIONS["ru"]).get(key, key)

THEMES = {
    "VOID": {
        "bg": "#080512",
        "surface": "#100a1b",
        "surface2": "#171025",
        "border": "#2c1f45",
        "text": "#f8f3ff",
        "muted": "#a79aba",
        "accent": "#a77cff",
        "accent2": "#d8c7ff",
        "search": "#fbfaff",
        "search_text": "#17111e",
    },
    "ICE": {
        "bg": "#071018",
        "surface": "#0d1a24",
        "surface2": "#142530",
        "border": "#2b4556",
        "text": "#f4fbff",
        "muted": "#93adba",
        "accent": "#59c9ff",
        "accent2": "#d6f3ff",
        "search": "#f7fbff",
        "search_text": "#101820",
    },
    "BLUE": {
        "bg": "#070b12",
        "surface": "#0e1622",
        "surface2": "#152139",
        "border": "#2a4162",
        "text": "#f4f8ff",
        "muted": "#94a8bf",
        "accent": "#638eff",
        "accent2": "#d9e4ff",
        "search": "#f8faff",
        "search_text": "#131925",
    },
    "PURPLE": {
        "bg": "#0d0714",
        "surface": "#170d22",
        "surface2": "#241430",
        "border": "#4a2c60",
        "text": "#fff6ff",
        "muted": "#b29dbd",
        "accent": "#c36dff",
        "accent2": "#f0dcff",
        "search": "#fcf9ff",
        "search_text": "#1c1322",
    },
}


def stylesheet(theme_name):
    theme = THEMES.get(theme_name, THEMES["VOID"])
    return f"""
    QWidget {{
        background: {theme['bg']};
        color: {theme['text']};
        font-family: "Segoe UI";
        font-size: 14px;
    }}

    QMainWindow {{
        background: {theme['bg']};
    }}

    QFrame#chromeBar {{
        background: rgba(12, 10, 20, 205);
        border: 1px solid rgba(90, 74, 120, 100);
        border-radius: 14px;
    }}

    QFrame#sidebar {{
        background: rgba(10, 8, 18, 238);
        border: 1px solid rgba(90, 74, 120, 65);
        border-radius: 18px;
    }}

    QPushButton {{
        background: transparent;
        color: {theme['muted']};
        border: 1px solid transparent;
        border-radius: 12px;
        padding: 10px 13px;
    }}

    QPushButton:hover {{
        background: {theme['surface2']};
        color: {theme['text']};
        border-color: {theme['border']};
    }}

    QPushButton[accent="true"] {{
        background: {theme['accent']};
        color: #160f20;
        border-color: {theme['accent']};
        font-weight: 700;
    }}

    QLineEdit {{
        background: {theme['surface']};
        color: {theme['text']};
        border: 1px solid {theme['border']};
        border-radius: 16px;
        padding: 11px 15px;
        selection-background-color: {theme['accent']};
        selection-color: #ffffff;
    }}

    QLineEdit:focus {{
        border-color: {theme['accent']};
    }}

    QFrame#mainSearch {{
        background: rgba(24, 18, 34, 150);
        border: 1px solid rgba(167,124,255,45);
        border-radius: 21px;
    }}

    QFrame#searchShell {{
        background: {theme['surface']};
        border: 1px solid {theme['border']};
        border-radius: 20px;
    }}

    QFrame#mainSearch QLineEdit {{
        background: transparent;
        color: {theme['text']};
        border: none;
        padding: 0 8px;
        font-size: 15px;
    }}

    QLabel#searchIcon {{
        color: {theme['muted']};
        font-size: 21px;
        font-weight: 700;
        padding-left: 3px;
    }}

    QPushButton#searchUtility {{
        background: rgba(255,255,255,18);
        color: {theme['muted']};
        border: 1px solid rgba(255,255,255,24);
        border-radius: 10px;
        font-size: 11px;
        font-weight: 700;
        padding: 6px 9px;
    }}

    QPushButton#searchUtility:hover {{
        color: {theme['accent']};
        background: rgba(30, 20, 45, 18);
        border: none;
    }}

    QPushButton#searchButton {{
        background: {theme['accent']};
        color: white;
        border-radius: 18px;
        font-size: 17px;
        font-weight: 700;
    }}

    QLabel#brandHero {{
        color: {theme['accent2']};
        font-size: 20px;
        font-weight: 850;
        letter-spacing: 4px;
    }}

    QLabel#creatorTop {{
        color: {theme['muted']};
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.4px;
        padding-left: 4px;
    }}

    QLabel#homeLogo {{
        color: {theme['accent2']};
        font-size: 56px;
        font-weight: 800;
        letter-spacing: 7px;
    }}

    QLabel#homeWelcome {{
        color: {theme['accent2']};
        font-size: 17px;
        font-weight: 700;
        letter-spacing: .6px;
    }}

    QLabel#homepageSub {{
        color: {theme['muted']};
        font-size: 11px;
        font-weight: 650;
        letter-spacing: 1.1px;
    }}

    QLabel#homepageSection {{
        color: {theme['text']};
        font-size: 13px;
        font-weight: 720;
    }}

    QLabel#shortcutCircle {{
        min-width: 52px;
        max-width: 52px;
        min-height: 52px;
        max-height: 52px;
        border-radius: 26px;
        font-size: 21px;
        font-weight: 800;
    }}

    QLabel#shortcutName {{
        color: {theme['muted']};
        font-size: 11px;
        font-weight: 700;
    }}

    QFrame#shortcutItem {{
        background: transparent;
        border: none;
    }}

    QFrame#quickShell {{
        background: rgba(22, 16, 33, 105);
        border: 1px solid rgba(167, 124, 255, 28);
        border-radius: 12px;
    }}

    QPushButton#addShortcut {{
        background: transparent;
        border: none;
        color: {theme['muted']};
        padding: 5px 7px;
        font-size: 11px;
        font-weight: 700;
    }}

    QPushButton#addShortcut:hover {{
        color: {theme['text']};
        background: rgba(167, 124, 255, 20);
    }}

    QPushButton#sidebarNav {{
        min-height: 43px;
        text-align: left;
        font-size: 13px;
        font-weight: 700;
        padding: 9px 12px;
        color: {theme['muted']};
        border-radius: 10px;
    }}

    QPushButton#sidebarNav:hover {{
        color: {theme['text']};
        background: {theme['surface2']};
        border-color: {theme['border']};
    }}

    QLabel#sidebarNavIcon {{
        font-size: 22px;
        font-weight: 700;
    }}

    QFrame#weatherCard {{
        background: {theme['surface2']};
        border: 1px solid {theme['border']};
        border-radius: 16px;
    }}

    QLabel#weatherTemp {{
        color: {theme['text']};
        font-size: 25px;
        font-weight: 800;
    }}

    QLabel#weatherCity {{
        color: {theme['text']};
        font-size: 14px;
        font-weight: 700;
    }}

    QLabel#weatherMeta {{
        color: {theme['muted']};
        font-size: 12px;
    }}

    QPushButton#weatherSearch {{
        background: transparent;
        color: {theme['accent2']};
        border: 1px solid {theme['border']};
        border-radius: 10px;
        padding: 7px 10px;
        font-size: 12px;
        font-weight: 700;
    }}

    QPushButton#accountButton {{
        background: rgba(255,255,255,10);
        border: 1px solid rgba(167,124,255,38);
        border-radius: 13px;
        color: {theme['text']};
        padding: 7px 10px;
        font-weight: 650;
    }}

    QTabWidget::pane {{
        border: none;
        background: transparent;
    }}

    QTabBar::tab {{
        background: {theme['surface']};
        color: {theme['muted']};
        border: 1px solid transparent;
        border-radius: 11px;
        padding: 10px 17px;
        margin-right: 5px;
        font-size: 13px;
        font-weight: 650;
    }}

    QTabBar::tab:selected {{
        background: {theme['surface2']};
        color: {theme['text']};
        border-color: {theme['border']};
    }}

    QComboBox {{
        background: {theme['surface']};
        color: {theme['text']};
        border: 1px solid {theme['border']};
        border-radius: 10px;
        padding: 8px;
    }}

    QComboBox QAbstractItemView {{
        background: {theme['surface']};
        color: {theme['text']};
        selection-background-color: {theme['accent']};
    }}

    QLabel#pageTitle {{
        color: {theme['text']};
        font-size: 30px;
        font-weight: 760;
    }}

    QLabel#section {{
        color: {theme['text']};
        font-size: 18px;
        font-weight: 700;
    }}

    QLabel#badge {{
        background: {theme['accent']};
        color: #170f20;
        border-radius: 9px;
        padding: 5px 9px;
        font-weight: 700;
    }}

    QFrame#settingCard, QFrame#card, QFrame#profileStat, QFrame#achievementCard {{
        background: {theme['surface']};
        border: 1px solid {theme['border']};
        border-radius: 15px;
    }}

    QLabel#settingTitle {{
        color: {theme['text']};
        font-size: 15px;
        font-weight: 750;
    }}

    QLabel#settingDescription {{
        color: {theme['muted']};
        font-size: 12px;
        line-height: 1.3;
    }}

    QListWidget {{
        background: transparent;
        border: none;
    }}

    QListWidget::item {{
        background: {theme['surface']};
        border: 1px solid {theme['border']};
        border-radius: 13px;
        padding: 12px;
        margin: 5px 0;
    }}

    QListWidget::item:selected {{
        background: {theme['surface2']};
        border-color: {theme['accent']};
    }}

    QLabel#profileName {{
        color: {theme['text']};
        font-size: 27px;
        font-weight: 800;
    }}

    QLabel#profileAvatar {{
        background: {theme['accent']};
        color: white;
        border-radius: 38px;
        min-width: 76px;
        max-width: 76px;
        min-height: 76px;
        max-height: 76px;
        font-size: 29px;
        font-weight: 800;
    }}

    QLabel#profileStatValue {{
        color: {theme['text']};
        font-size: 23px;
        font-weight: 800;
    }}

    QLabel#founderBadge {{
        color: {theme['accent2']};
        font-weight: 700;
    }}

    QLabel#achievementIcon {{
        min-width: 34px;
        max-width: 34px;
        min-height: 34px;
        max-height: 34px;
        border-radius: 17px;
        background: rgba(167,124,255,35);
        color: {theme['accent2']};
        font-size: 18px;
        qproperty-alignment: AlignCenter;
    }}

    QLabel#achievementTitle {{
        color: {theme['text']};
        font-size: 16px;
        font-weight: 760;
    }}

    QLabel#achievementDesc {{
        color: {theme['text']};
        font-size: 13px;
    }}

    QLabel#achievementDone {{
        color: #79e6b2;
        background: rgba(55, 180, 125, 30);
        border: 1px solid rgba(55, 180, 125, 80);
        border-radius: 8px;
        padding: 4px 8px;
        font-size: 11px;
        font-weight: 700;
    }}

    QLabel#achievementProgress {{
        color: {theme['muted']};
        background: rgba(255,255,255,15);
        border: 1px solid rgba(255,255,255,18);
        border-radius: 8px;
        padding: 4px 8px;
        font-size: 11px;
        font-weight: 700;
    }}

    QLabel#achievementProgressText {{
        color: {theme['accent2']};
        font-size: 11px;
        font-weight: 700;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 9px;
    }}

    QScrollBar::handle:vertical {{
        background: {theme['border']};
        border-radius: 4px;
        min-height: 30px;
    }}
    """


def fade_in(widget, duration=180):
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    widget._orbit_fade_animation = animation
    widget._orbit_fade_effect = effect
