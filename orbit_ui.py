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
        "auto_update": "Автоматические обновления", "animations": "Плавные анимации", "support": "Помощь", "gemini": "Orbit AI", "admin_panel": "Админ-панель",
    },
    "en": {
        "home": "Home", "tabs": "Tabs", "history": "History", "bookmarks": "Bookmarks",
        "downloads": "Downloads", "notes": "Notes", "settings": "Settings", "search": "Search or enter address",
        "quick": "Quick access", "add": "Add", "welcome": "Welcome to Orbit",
        "future": "B R O W S E   T H E   F U T U R E", "weather": "Weather", "profile": "Profile",
        "language": "Interface language", "appearance": "Appearance", "behavior": "Behavior",
        "search_engine": "Search engine", "site_theming": "Apply Orbit style to websites",
        "auto_update": "Automatic updates", "animations": "Smooth animations", "support": "Support", "gemini": "Orbit AI", "admin_panel": "Admin panel",
    },

    "de": {
        "home": "Startseite", "tabs": "Tabs", "history": "Verlauf", "bookmarks": "Lesezeichen",
        "downloads": "Downloads", "notes": "Notizen", "settings": "Einstellungen", "search": "Suche oder Adresse",
        "quick": "Schnellzugriff", "add": "Hinzufügen", "welcome": "Willkommen bei Orbit",
        "future": "B R O W S E   T H E   F U T U R E", "weather": "Wetter", "profile": "Profil",
        "language": "Sprache", "appearance": "Darstellung", "behavior": "Verhalten",
        "search_engine": "Suchmaschine", "site_theming": "Orbit-Stil für Webseiten",
        "auto_update": "Automatische Updates", "animations": "Sanfte Animationen", "support": "Hilfe", "gemini": "Orbit AI", "admin_panel": "Admin-Bereich",
    },
    "es": {
        "home": "Inicio", "tabs": "Pestañas", "history": "Historial", "bookmarks": "Marcadores",
        "downloads": "Descargas", "notes": "Notas", "settings": "Ajustes", "search": "Buscar o introducir dirección",
        "quick": "Acceso rápido", "add": "Añadir", "welcome": "Bienvenido a Orbit",
        "future": "B R O W S E   T H E   F U T U R E", "weather": "Tiempo", "profile": "Perfil",
        "language": "Idioma", "appearance": "Apariencia", "behavior": "Comportamiento",
        "search_engine": "Motor de búsqueda", "site_theming": "Estilo Orbit en sitios",
        "auto_update": "Actualizaciones automáticas", "animations": "Animaciones suaves", "support": "Ayuda", "gemini": "Orbit AI", "admin_panel": "Panel de administración",
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
    "CYBER": {
        "bg": "#050913",
        "surface": "#0a1222",
        "surface2": "#101d36",
        "border": "#214570",
        "text": "#f4f9ff",
        "muted": "#91a7c4",
        "accent": "#39b8ff",
        "accent2": "#b98cff",
        "search": "#f8fbff",
        "search_text": "#0b1120",
    },
    "SUNSET": {
        "bg": "#10070d",
        "surface": "#1d0d18",
        "surface2": "#301323",
        "border": "#5b2948",
        "text": "#fff5fb",
        "muted": "#c19aaa",
        "accent": "#ff5fb0",
        "accent2": "#ff9bca",
        "search": "#fff8fc",
        "search_text": "#22101a",
    },
    "EMERALD": {
        "bg": "#04100d",
        "surface": "#091914",
        "surface2": "#10271e",
        "border": "#214b3b",
        "text": "#effff7",
        "muted": "#91b1a2",
        "accent": "#44e8a0",
        "accent2": "#b3ffe0",
        "search": "#f7fffb",
        "search_text": "#0d1914",
    },
    "RED": {
        "bg": "#100709",
        "surface": "#1e0d12",
        "surface2": "#32141d",
        "border": "#5b2b36",
        "text": "#fff4f6",
        "muted": "#c29aa3",
        "accent": "#ff5274",
        "accent2": "#ffb0be",
        "search": "#fff9fa",
        "search_text": "#241117",
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

    QLabel {{
        background: transparent;
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
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 rgba(40,96,255,42), stop:0.52 rgba(94,62,255,50), stop:1 rgba(210,70,255,34));
        border: 1px solid rgba(116,145,255,90);
        border-radius: 22px;
    }}

    QFrame#searchShell {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {theme['surface']}, stop:0.5 {theme['surface2']}, stop:1 {theme['surface']});
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
        font-size: 19px;
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
        border-radius: 20px;
        font-size: 18px;
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
        font-size: 12px;
        font-weight: 650;
        letter-spacing: 1.1px;
    }}

    QLabel#homepageSection {{
        color: {theme['text']};
        font-size: 13px;
        font-weight: 720;
    }}

    QLabel#shortcutCircle {{
        min-width: 48px;
        max-width: 48px;
        min-height: 48px;
        max-height: 48px;
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
        background: rgba(22, 16, 33, 76);
        border: 1px solid rgba(167, 124, 255, 22);
        border-radius: 11px;
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
        min-height: 50px;
        text-align: left;
        font-size: 14px;
        font-weight: 750;
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
        background: rgba(16, 10, 27, 170);
        color: {theme['muted']};
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 8px 14px;
        margin: 3px 4px 0 0;
        min-width: 92px;
        font-size: 12px;
        font-weight: 700;
    }}

    QTabBar::tab:selected {{
        background: {theme['surface2']};
        color: {theme['text']};
        border-color: {theme['border']};
    }}

    QTabBar::close-button {{
        width: 18px;
        height: 18px;
        margin-left: 6px;
    }}

    QPushButton#tabCloseButton {{
        background: transparent;
        border: none;
        color: {theme['muted']};
        border-radius: 8px;
        padding: 0px;
        font-size: 16px;
        font-weight: 700;
    }}

    QPushButton#tabCloseButton:hover {{
        background: rgba(255, 255, 255, 18);
        color: {theme['text']};
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

    QFrame#settingCard, QFrame#card, QFrame#profileStat {{
        background: {theme['surface']};
        border: 1px solid {theme['border']};
        border-radius: 15px;
    }}

    QFrame#achievementCard {{
        background: rgba(13, 23, 32, 235);
        border: 1px solid {theme['border']};
        border-radius: 18px;
    }}

    QFrame#achievementCard[done="true"] {{
        background: rgba(20, 39, 37, 235);
        border-color: rgba(70, 218, 164, 110);
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
        border: none;
        outline: none;
        color: {theme['text']};
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
        font-weight: 800;
        padding: 0;
    }}

    QLabel#achievementDesc {{
        color: {theme['text']};
        font-size: 12px;
        padding: 0;
    }}

    QLabel#achievementDone {{
        color: #79e6b2;
        background: rgba(55, 180, 125, 30);
        border: 1px solid rgba(55, 180, 125, 80);
        border-radius: 8px;
        padding: 3px 7px;
        font-size: 10px;
        font-weight: 750;
    }}

    QLabel#achievementProgress {{
        color: {theme['muted']};
        background: rgba(255,255,255,15);
        border: 1px solid rgba(255,255,255,18);
        border-radius: 8px;
        padding: 3px 7px;
        font-size: 10px;
        font-weight: 750;
    }}

    QLabel#achievementReward {{
        color: {theme['muted']};
        font-size: 11px;
        font-weight: 650;
        padding: 4px 7px;
        background: rgba(167, 124, 255, 16);
        border: 1px solid rgba(167, 124, 255, 28);
        border-radius: 8px;
    }}

    QLabel#achievementProgressText {{
        color: {theme['accent2']};
        font-size: 11px;
        font-weight: 750;
        padding: 0;
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
    QFrame#aiHeader {{
        background: {theme['surface']};
        border: 1px solid {theme['border']};
        border-radius: 18px;
    }}

    QLabel#aiTitle {{
        color: {theme['accent2']};
        font-size: 24px;
        font-weight: 800;
    }}

    QLabel#aiSubtitle, QLabel#aiStatus, QLabel#aiAttachmentLabel {{
        color: {theme['muted']};
        font-size: 12px;
    }}

    QListWidget#aiChat {{
        background: transparent;
        border: none;
        outline: none;
        padding: 4px;
    }}

    QFrame#aiMessageUser, QFrame#aiMessageAssistant {{
        border-radius: 16px;
        border: 1px solid {theme['border']};
    }}

    QFrame#aiMessageUser {{
        background: rgba(82, 64, 130, 80);
        margin-left: 120px;
    }}

    QFrame#aiMessageAssistant {{
        background: {theme['surface']};
        margin-right: 120px;
    }}

    QLabel#aiMessageAuthor {{
        color: {theme['accent']};
        font-size: 11px;
        font-weight: 800;
    }}

    QLabel#aiMessageText {{
        color: {theme['text']};
        font-size: 14px;
        line-height: 1.4;
    }}

    QLabel#aiImageChip {{
        background: {theme['surface2']};
        border: 1px solid {theme['border']};
        border-radius: 8px;
        padding: 5px 8px;
        color: {theme['muted']};
    }}

    QFrame#aiComposer {{
        background: {theme['surface']};
        border: 1px solid {theme['border']};
        border-radius: 18px;
    }}

    QTextEdit#aiInput {{
        background: transparent;
        border: none;
        color: {theme['text']};
        font-size: 14px;
        padding: 8px;
    }}

    QPushButton#aiSend {{
        background: {theme['accent']};
        color: #160f20;
        border: none;
        border-radius: 27px;
        font-size: 24px;
        font-weight: 800;
    }}


    QPushButton#aiQuickAction {{
        background: {theme['surface2']};
        color: {theme['text']};
        border: 1px solid {theme['border']};
        border-radius: 10px;
        padding: 7px 11px;
        font-size: 12px;
        font-weight: 650;
    }}
    QPushButton#aiQuickAction:hover {{
        background: {theme['accent']};
        color: #120d1b;
    }}

    QListWidget#supportList, QListWidget#supportQueue {{
        background: transparent;
        border: none;
    }}

    QPushButton#aiAttachment {{
        background: {theme['surface2']};
        color: {theme['text']};
        border: 1px solid {theme['border']};
        border-radius: 10px;
        padding: 8px 12px;
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
