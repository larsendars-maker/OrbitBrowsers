import json
import os
import sys

import requests

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFrame,
)
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView


# ============================================================
# ORBIT
# ============================================================

APP_NAME = "Orbit Browser"
API_URL = "https://orbit-api-9uqa.onrender.com"


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = os.path.join(
    os.environ.get(
        "LOCALAPPDATA",
        os.path.expanduser("~"),
    ),
    "OrbitBrowser",
)

DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
PROFILES_DIR = os.path.join(BASE_DIR, "profiles")
THEMES_DIR = os.path.join(BASE_DIR, "themes")
NOTES_DIR = os.path.join(BASE_DIR, "notes")
WORKSPACES_DIR = os.path.join(BASE_DIR, "workspaces")
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")

CONFIG_FILE = os.path.join(
    CONFIG_DIR,
    "config.json",
)

SESSION_FILE = os.path.join(
    DATA_DIR,
    "session.json",
)


# ============================================================
# THEMES
# ============================================================

THEMES = {
    "VOID": {
        "bg": "#080b12",
        "panel": "#101521",
        "panel2": "#171f2e",
        "border": "#2b3548",
        "text": "#f4f6ff",
        "muted": "#8b97ab",
        "accent": "#7657ff",
        "accent2": "#9a85ff",
    },
    "ICE": {
        "bg": "#071018",
        "panel": "#0d1b27",
        "panel2": "#14293b",
        "border": "#2b4a61",
        "text": "#effaff",
        "muted": "#91b1c4",
        "accent": "#41c7ff",
        "accent2": "#75dcff",
    },
    "EMERALD": {
        "bg": "#06110d",
        "panel": "#0c1914",
        "panel2": "#12251d",
        "border": "#2a4e3e",
        "text": "#f0fff7",
        "muted": "#8daf9f",
        "accent": "#2ddc8a",
        "accent2": "#69f0ad",
    },
    "PURPLE": {
        "bg": "#0d0715",
        "panel": "#180e24",
        "panel2": "#241434",
        "border": "#51326c",
        "text": "#fff6ff",
        "muted": "#b39abb",
        "accent": "#c15cff",
        "accent2": "#de8aff",
    },
    "RED": {
        "bg": "#120809",
        "panel": "#211011",
        "panel2": "#321719",
        "border": "#603033",
        "text": "#fff5f5",
        "muted": "#c19b9d",
        "accent": "#ff5069",
        "accent2": "#ff7b8d",
    },
    "BLUE": {
        "bg": "#060b15",
        "panel": "#0d1625",
        "panel2": "#14213a",
        "border": "#2a466d",
        "text": "#f2f7ff",
        "muted": "#91a6c3",
        "accent": "#4d8dff",
        "accent2": "#79aaff",
    },
}


# ============================================================
# ACHIEVEMENTS
# ============================================================

ACHIEVEMENTS = [
    {
        "name": "First Flight",
        "description": "Первый запуск Orbit",
        "icon": "🚀",
        "xp": 100,
    },
    {
        "name": "Explorer",
        "description": "Исследователь Orbit",
        "icon": "🌌",
        "xp": 250,
    },
    {
        "name": "Power User",
        "description": "Продвинутый пользователь",
        "icon": "⚡",
        "xp": 500,
    },
    {
        "name": "Creator",
        "description": "Создатель контента",
        "icon": "✦",
        "xp": 750,
    },
    {
        "name": "Founder",
        "description": "Создатель Orbit",
        "icon": "👑",
        "xp": 1000,
    },
]


# ============================================================
# FILESYSTEM
# ============================================================

def create_directories():
    for directory in [
        BASE_DIR,
        DATA_DIR,
        CONFIG_DIR,
        PROFILES_DIR,
        THEMES_DIR,
        NOTES_DIR,
        WORKSPACES_DIR,
        DOWNLOADS_DIR,
        CACHE_DIR,
        LOGS_DIR,
        BACKUPS_DIR,
    ]:
        os.makedirs(
            directory,
            exist_ok=True,
        )


# ============================================================
# CONFIG
# ============================================================

def save_config(config):
    create_directories()

    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            config,
            file,
            ensure_ascii=False,
            indent=4,
        )


def load_config():
    create_directories()

    config = {}

    if os.path.exists(CONFIG_FILE):
        try:
            with open(
                CONFIG_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                config = json.load(file)

            if not isinstance(config, dict):
                config = {}

        except Exception:
            config = {}

    config.setdefault(
        "theme",
        "VOID",
    )

    config.setdefault(
        "search_engine",
        "https://www.google.com/search?q=",
    )

    config["api_url"] = API_URL

    if config["theme"] not in THEMES:
        config["theme"] = "VOID"

    save_config(config)

    return config


# ============================================================
# SESSION
# ============================================================

def save_session(token, user):
    create_directories()

    with open(
        SESSION_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "token": token,
                "user": user,
            },
            file,
            ensure_ascii=False,
            indent=4,
        )


def clear_session():
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
    except Exception:
        pass


def load_saved_session(api_url):
    if not os.path.exists(SESSION_FILE):
        return None

    try:
        with open(
            SESSION_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            session = json.load(file)

        token = session.get("token")

        if not token:
            clear_session()
            return None

        response = requests.get(
            f"{api_url}/api/auth/session",
            headers={
                "Authorization": f"Bearer {token}",
            },
            timeout=15,
        )

        if response.status_code != 200:
            clear_session()
            return None

        data = response.json()

        if not data.get("ok"):
            clear_session()
            return None

        user = data.get("user")

        if not user:
            clear_session()
            return None

        save_session(
            token,
            user,
        )

        return {
            "token": token,
            "user": user,
        }

    except Exception:
        clear_session()
        return None


# ============================================================
# API
# ============================================================

def post_api(
    api_url,
    endpoint,
    payload,
    token=None,
):
    headers = {}

    if token:
        headers["Authorization"] = (
            f"Bearer {token}"
        )

    return requests.post(
        f"{api_url.rstrip('/')}{endpoint}",
        json=payload,
        headers=headers,
        timeout=20,
    )


def patch_api(
    api_url,
    endpoint,
    payload,
    token,
):
    return requests.patch(
        f"{api_url.rstrip('/')}{endpoint}",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
        },
        timeout=20,
    )


# ============================================================
# STYLES
# ============================================================

def theme_styles(theme):
    t = THEMES[theme]

    return f"""
    QWidget {{
        background: {t["bg"]};
        color: {t["text"]};
        font-family: "Segoe UI";
    }}

    QMainWindow {{
        background: {t["bg"]};
    }}

    QLineEdit {{
        background: {t["panel"]};
        border: 1px solid {t["border"]};
        border-radius: 14px;
        padding: 11px 15px;
        color: {t["text"]};
        font-size: 14px;
    }}

    QLineEdit:focus {{
        border: 1px solid {t["accent"]};
    }}

    QPushButton {{
        background: {t["panel"]};
        border: 1px solid {t["border"]};
        border-radius: 11px;
        padding: 9px 13px;
        color: {t["text"]};
        font-size: 13px;
    }}

    QPushButton:hover {{
        background: {t["panel2"]};
        border-color: {t["accent"]};
    }}

    QPushButton[accent="true"] {{
        background: {t["accent"]};
        border-color: {t["accent"]};
        color: white;
        font-weight: 700;
    }}

    QPushButton[accent="true"]:hover {{
        background: {t["accent2"]};
    }}

    QComboBox {{
        background: {t["panel"]};
        border: 1px solid {t["border"]};
        border-radius: 10px;
        padding: 8px 12px;
        color: {t["text"]};
    }}

    QComboBox QAbstractItemView {{
        background: {t["panel"]};
        color: {t["text"]};
        selection-background-color: {t["accent"]};
    }}

    QFrame#sidebar {{
        background: {t["panel"]};
        border-right: 1px solid {t["border"]};
    }}

    QFrame#card {{
        background: {t["panel"]};
        border: 1px solid {t["border"]};
        border-radius: 18px;
    }}

    QFrame#hero {{
        background: {t["panel"]};
        border: 1px solid {t["border"]};
        border-radius: 22px;
    }}

    QLabel#logo {{
        font-size: 25px;
        font-weight: 900;
        color: {t["accent"]};
        letter-spacing: 2px;
    }}

    QLabel#heroTitle {{
        font-size: 43px;
        font-weight: 800;
    }}

    QLabel#subtitle {{
        color: {t["muted"]};
        font-size: 15px;
    }}

    QLabel#section {{
        font-size: 18px;
        font-weight: 700;
    }}

    QLabel#muted {{
        color: {t["muted"]};
    }}

    QLabel#badge {{
        background: {t["accent"]};
        color: white;
        border-radius: 8px;
        padding: 5px 9px;
        font-weight: 700;
    }}
    """


# ============================================================
# AUTH
# ============================================================

class AuthWindow(QDialog):
    def __init__(self, api_url):
        super().__init__()

        self.api_url = api_url
        self.session = None

        self.setWindowTitle(
            "Orbit Browser"
        )

        self.setMinimumSize(
            470,
            430,
        )

        self.setStyleSheet(
            theme_styles("VOID")
        )

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            35,
            30,
            35,
            30,
        )

        logo = QLabel("ORBIT")
        logo.setObjectName("logo")
        logo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(logo)

        title = QLabel(
            "Welcome"
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title.setStyleSheet(
            "font-size: 27px; font-weight: 800;"
        )

        layout.addWidget(title)

        subtitle = QLabel(
            "Ваш персональный браузер"
        )

        subtitle.setObjectName(
            "subtitle"
        )

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(subtitle)

        form = QFormLayout()

        form.setSpacing(12)

        self.username = QLineEdit()
        self.username.setPlaceholderText(
            "Имя пользователя"
        )

        self.email = QLineEdit()
        self.email.setPlaceholderText(
            "Email"
        )

        self.password = QLineEdit()
        self.password.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.password.setPlaceholderText(
            "Пароль"
        )

        form.addRow(
            "Имя:",
            self.username,
        )

        form.addRow(
            "Email:",
            self.email,
        )

        form.addRow(
            "Пароль:",
            self.password,
        )

        layout.addLayout(form)

        buttons = QHBoxLayout()

        register_button = QPushButton(
            "Создать аккаунт"
        )

        register_button.setProperty(
            "accent",
            True,
        )

        login_button = QPushButton(
            "Войти"
        )

        buttons.addWidget(register_button)
        buttons.addWidget(login_button)

        layout.addLayout(buttons)

        self.status = QLabel()

        self.status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status.setWordWrap(True)

        layout.addWidget(self.status)

        register_button.clicked.connect(
            self.register
        )

        login_button.clicked.connect(
            self.login
        )

    def register(self):
        username = self.username.text().strip()
        email = self.email.text().strip()
        password = self.password.text()

        if len(username) < 3:
            self.status.setText(
                "Имя должно содержать минимум 3 символа."
            )
            return

        if not email:
            self.status.setText(
                "Введите email."
            )
            return

        if len(password) < 6:
            self.status.setText(
                "Пароль должен содержать минимум 6 символов."
            )
            return

        self.status.setText(
            "Создание аккаунта..."
        )

        try:
            response = post_api(
                self.api_url,
                "/api/auth/register",
                {
                    "username": username,
                    "email": email,
                    "password": password,
                },
            )

            if response.status_code == 200:
                data = response.json()

                save_session(
                    data["token"],
                    data["user"],
                )

                self.session = {
                    "token": data["token"],
                    "user": data["user"],
                }

                self.accept()
                return

            self.show_error(
                response,
                "Ошибка регистрации",
            )

        except Exception as error:
            self.status.setText(
                f"Ошибка подключения: {error}"
            )

    def login(self):
        email = self.email.text().strip()
        password = self.password.text()

        if not email or not password:
            self.status.setText(
                "Введите email и пароль."
            )
            return

        self.status.setText(
            "Вход..."
        )

        try:
            response = post_api(
                self.api_url,
                "/api/auth/login",
                {
                    "email": email,
                    "password": password,
                },
            )

            if response.status_code == 200:
                data = response.json()

                save_session(
                    data["token"],
                    data["user"],
                )

                self.session = {
                    "token": data["token"],
                    "user": data["user"],
                }

                self.accept()
                return

            self.show_error(
                response,
                "Ошибка входа",
            )

        except Exception as error:
            self.status.setText(
                f"Ошибка подключения: {error}"
            )

    def show_error(self, response, default):
        try:
            data = response.json()

            detail = data.get(
                "detail",
                default,
            )

        except Exception:
            detail = response.text or default

        self.status.setText(
            f"{detail} [{response.status_code}]"
        )


# ============================================================
# PROFILE WINDOW
# ============================================================

class ProfileDialog(QDialog):
    def __init__(self, window):
        super().__init__()

        self.window = window
        self.user = window.user

        self.setWindowTitle(
            "Orbit Profile"
        )

        self.setMinimumSize(
            620,
            600,
        )

        self.setStyleSheet(
            theme_styles(
                window.current_theme
            )
        )

        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)

        header = QHBoxLayout()

        avatar = QLabel("◎")

        avatar.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        avatar.setFixedSize(
            90,
            90,
        )

        avatar.setStyleSheet(
            """
            font-size: 48px;
            font-weight: 800;
            border-radius: 45px;
            background: #20283a;
            """
        )

        header.addWidget(avatar)

        info = QVBoxLayout()

        display_name = self.user.get(
            "display_name",
            self.user.get(
                "username",
                "User",
            ),
        )

        self.name_label = QLabel(
            display_name
        )

        self.name_label.setStyleSheet(
            "font-size: 24px; font-weight: 800;"
        )

        info.addWidget(
            self.name_label
        )

        username = self.user.get(
            "username",
            "User",
        )

        info.addWidget(
            QLabel(f"@{username}")
        )

        role = self.user.get(
            "role",
            "user",
        )

        if role == "founder":
            badge = QLabel(
                "👑 FOUNDER • CREATOR OF ORBIT"
            )

            badge.setObjectName(
                "badge"
            )

            info.addWidget(
                badge
            )

        else:
            title = self.user.get(
                "title",
                "Explorer",
            )

            info.addWidget(
                QLabel(title)
            )

        header.addLayout(info)
        header.addStretch()

        layout.addLayout(header)

        xp = int(
            self.user.get(
                "xp",
                0,
            )
        )

        level = max(
            1,
            xp // 500 + 1,
        )

        xp_in_level = xp % 500

        level_label = QLabel(
            f"LEVEL {level}    •    {xp} XP"
        )

        level_label.setStyleSheet(
            "font-size: 17px; font-weight: 700;"
        )

        layout.addWidget(
            level_label
        )

        progress_text = QLabel(
            f"{xp_in_level}/500 XP до следующего уровня"
        )

        progress_text.setObjectName(
            "muted"
        )

        layout.addWidget(
            progress_text
        )

        bio_label = QLabel(
            self.user.get(
                "bio",
                "",
            )
            or "Описание профиля не добавлено."
        )

        bio_label.setWordWrap(True)

        layout.addWidget(
            bio_label
        )

        section = QLabel(
            "ACHIEVEMENTS"
        )

        section.setObjectName(
            "section"
        )

        layout.addWidget(section)

        achievements = QGridLayout()

        unlocked_count = min(
            len(ACHIEVEMENTS),
            max(1, xp // 250),
        )

        for index, achievement in enumerate(
            ACHIEVEMENTS
        ):
            card = QFrame()

            card.setObjectName(
                "card"
            )

            card_layout = QVBoxLayout(
                card
            )

            title = QLabel(
                f'{achievement["icon"]}  {achievement["name"]}'
            )

            title.setStyleSheet(
                "font-weight: 700;"
            )

            desc = QLabel(
                achievement["description"]
            )

            desc.setObjectName(
                "muted"
            )

            card_layout.addWidget(
                title
            )

            card_layout.addWidget(
                desc
            )

            if index < unlocked_count:
                unlocked = QLabel(
                    "UNLOCKED"
                )

                unlocked.setObjectName(
                    "badge"
                )

                card_layout.addWidget(
                    unlocked
                )

            else:
                locked = QLabel(
                    "LOCKED"
                )

                locked.setObjectName(
                    "muted"
                )

                card_layout.addWidget(
                    locked
                )

            achievements.addWidget(
                card,
                index // 2,
                index % 2,
            )

        layout.addLayout(
            achievements
        )

        edit_button = QPushButton(
            "Настроить профиль"
        )

        edit_button.setProperty(
            "accent",
            True,
        )

        edit_button.clicked.connect(
            self.edit_profile
        )

        layout.addWidget(
            edit_button
        )

    def edit_profile(self):
        dialog = EditProfileDialog(
            self.window
        )

        if (
            dialog.exec()
            == QDialog.DialogCode.Accepted
        ):
            self.accept()


# ============================================================
# EDIT PROFILE
# ============================================================

class EditProfileDialog(QDialog):
    def __init__(self, window):
        super().__init__()

        self.window = window
        self.setWindowTitle(
            "Edit Orbit Profile"
        )

        self.setMinimumSize(
            480,
            410,
        )

        self.setStyleSheet(
            theme_styles(
                window.current_theme
            )
        )

        layout = QVBoxLayout(self)

        title = QLabel(
            "Настройка профиля"
        )

        title.setStyleSheet(
            "font-size: 23px; font-weight: 800;"
        )

        layout.addWidget(title)

        form = QFormLayout()

        self.display_name = QLineEdit(
            self.window.user.get(
                "display_name",
                self.window.user.get(
                    "username",
                    "",
                ),
            )
        )

        self.bio = QLineEdit(
            self.window.user.get(
                "bio",
                "",
            )
        )

        self.title_edit = QLineEdit(
            self.window.user.get(
                "title",
                "Explorer",
            )
        )

        self.theme = QComboBox()

        self.theme.addItems(
            THEMES.keys()
        )

        self.theme.setCurrentText(
            self.window.user.get(
                "profile_theme",
                self.window.current_theme,
            )
        )

        form.addRow(
            "Имя:",
            self.display_name,
        )

        form.addRow(
            "Описание:",
            self.bio,
        )

        form.addRow(
            "Титул:",
            self.title_edit,
        )

        form.addRow(
            "Тема профиля:",
            self.theme,
        )

        layout.addLayout(form)

        save_button = QPushButton(
            "Сохранить"
        )

        save_button.setProperty(
            "accent",
            True,
        )

        layout.addWidget(
            save_button
        )

        save_button.clicked.connect(
            self.save
        )

    def save(self):
        payload = {
            "display_name": (
                self.display_name.text().strip()
            ),
            "bio": (
                self.bio.text().strip()
            ),
            "title": (
                self.title_edit.text().strip()
            ),
            "profile_theme": (
                self.theme.currentText()
            ),
        }

        try:
            response = patch_api(
                self.window.api_url,
                "/api/profile",
                payload,
                self.window.token,
            )

            if response.status_code != 200:
                QMessageBox.warning(
                    self,
                    "Orbit",
                    response.text,
                )
                return

            data = response.json()

            if not data.get("ok"):
                return

            self.window.user = data["user"]

            save_session(
                self.window.token,
                self.window.user,
            )

            self.accept()

        except Exception as error:
            QMessageBox.warning(
                self,
                "Orbit",
                f"Ошибка: {error}",
            )


# ============================================================
# HOME
# ============================================================

class HomePage(QWidget):
    def __init__(self, window):
        super().__init__()

        self.window = window

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            40,
            35,
            40,
            35,
        )

        layout.setSpacing(20)

        top = QHBoxLayout()

        logo = QLabel(
            "ORBIT"
        )

        logo.setObjectName(
            "logo"
        )

        top.addWidget(
            logo
        )

        top.addStretch()

        welcome_user = self.window.user.get(
            "display_name",
            self.window.user.get(
                "username",
                "User",
            ),
        )

        top_user = QLabel(
            f"● {welcome_user}"
        )

        top_user.setStyleSheet(
            "font-size: 14px; font-weight: 700;"
        )

        top.addWidget(
            top_user
        )

        layout.addLayout(top)

        hero = QFrame()

        hero.setObjectName(
            "hero"
        )

        hero_layout = QVBoxLayout(
            hero
        )

        hero_layout.setContentsMargins(
            35,
            30,
            35,
            30,
        )

        welcome = QLabel(
            "Welcome"
        )

        welcome.setObjectName(
            "heroTitle"
        )

        welcome.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        hero_layout.addWidget(
            welcome
        )

        subtitle = QLabel(
            "Добро пожаловать в Orbit Browser"
        )

        subtitle.setObjectName(
            "subtitle"
        )

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        hero_layout.addWidget(
            subtitle
        )

        hero_layout.addSpacing(
            15
        )

        self.search = QLineEdit()

        self.search.setPlaceholderText(
            "Поиск в интернете или введите адрес сайта..."
        )

        self.search.setMinimumHeight(
            55
        )

        hero_layout.addWidget(
            self.search
        )

        layout.addWidget(
            hero
        )

        sites_title = QLabel(
            "Быстрый доступ"
        )

        sites_title.setObjectName(
            "section"
        )

        layout.addWidget(
            sites_title
        )

        sites = QGridLayout()

        quick_sites = [
            ("Google", "https://google.com"),
            ("YouTube", "https://youtube.com"),
            ("GitHub", "https://github.com"),
            ("Discord", "https://discord.com"),
            ("Steam", "https://store.steampowered.com"),
            ("Gmail", "https://mail.google.com"),
        ]

        for index, (name, url) in enumerate(
            quick_sites
        ):
            button = QPushButton(
                name
            )

            button.setMinimumHeight(
                55
            )

            button.clicked.connect(
                lambda checked=False, u=url:
                self.window.open_url(u)
            )

            sites.addWidget(
                button,
                index // 3,
                index % 3,
            )

        layout.addLayout(
            sites
        )

        actions_title = QLabel(
            "Orbit"
        )

        actions_title.setObjectName(
            "section"
        )

        layout.addWidget(
            actions_title
        )

        actions = QHBoxLayout()

        for text, callback in [
            ("✦ Studio", self.window.open_studio),
            ("◉ VPN", self.window.open_vpn),
            ("▦ Workspaces", self.window.open_workspaces),
            ("◆ Notes", self.window.open_notes),
            ("● Profile", self.window.open_profile),
        ]:
            button = QPushButton(text)

            button.clicked.connect(
                callback
            )

            actions.addWidget(
                button
            )

        layout.addLayout(
            actions
        )

        layout.addStretch()

        self.search.returnPressed.connect(
            self.search_web
        )

    def search_web(self):
        text = (
            self.search.text().strip()
        )

        if not text:
            return

        if text.startswith(
            "http://"
        ) or text.startswith(
            "https://"
        ):
            url = text

        elif "." in text and " " not in text:
            url = f"https://{text}"

        else:
            url = (
                "https://www.google.com/search?q="
                + requests.utils.quote(text)
            )

        self.window.open_url(
            url
        )


# ============================================================
# BROWSER
# ============================================================

class BrowserView(QWebEngineView):
    def __init__(self):
        super().__init__()

        settings = self.settings()

        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled,
            True,
        )

        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalStorageEnabled,
            True,
        )

        settings.setAttribute(
            QWebEngineSettings.WebAttribute.FullScreenSupportEnabled,
            True,
        )


# ============================================================
# MAIN WINDOW
# ============================================================

class MainWindow(QMainWindow):
    def __init__(
        self,
        api_url,
        session,
        config,
    ):
        super().__init__()

        self.api_url = api_url
        self.session = session
        self.token = session["token"]
        self.user = session["user"]
        self.config = config

        self.current_theme = config.get(
            "theme",
            "VOID",
        )

        self.browser = BrowserView()
        self.home_page = HomePage(
            self
        )

        self.setWindowTitle(
            "Orbit Browser"
        )

        self.resize(
            1500,
            900,
        )

        self.build_ui()
        self.apply_theme()

    def build_ui(self):
        central = QWidget()

        self.setCentralWidget(
            central
        )

        root = QHBoxLayout(
            central
        )

        root.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        root.setSpacing(
            0
        )

        sidebar = QFrame()

        sidebar.setObjectName(
            "sidebar"
        )

        sidebar.setFixedWidth(
            220
        )

        sidebar_layout = QVBoxLayout(
            sidebar
        )

        sidebar_layout.setContentsMargins(
            14,
            18,
            14,
            18,
        )

        logo = QLabel(
            "ORBIT"
        )

        logo.setObjectName(
            "logo"
        )

        sidebar_layout.addWidget(
            logo
        )

        profile_name = self.user.get(
            "display_name",
            self.user.get(
                "username",
                "User",
            ),
        )

        user_button = QPushButton(
            f"●  {profile_name}"
        )

        user_button.clicked.connect(
            self.open_profile
        )

        sidebar_layout.addWidget(
            user_button
        )

        separator = QFrame()

        separator.setFrameShape(
            QFrame.Shape.HLine
        )

        sidebar_layout.addWidget(
            separator
        )

        menu = [
            ("⌂  Главная", self.show_home),
            ("＋  Новая вкладка", self.new_tab),
            ("✦  Orbit Studio", self.open_studio),
            ("◉  Orbit VPN", self.open_vpn),
            ("▦  Workspaces", self.open_workspaces),
            ("◆  Notes", self.open_notes),
            ("●  Профиль", self.open_profile),
        ]

        for text, callback in menu:
            button = QPushButton(
                text
            )

            button.clicked.connect(
                callback
            )

            sidebar_layout.addWidget(
                button
            )

        sidebar_layout.addStretch()

        theme_label = QLabel(
            "Тема интерфейса"
        )

        theme_label.setObjectName(
            "muted"
        )

        sidebar_layout.addWidget(
            theme_label
        )

        self.theme_combo = QComboBox()

        self.theme_combo.addItems(
            THEMES.keys()
        )

        self.theme_combo.setCurrentText(
            self.current_theme
        )

        self.theme_combo.currentTextChanged.connect(
            self.change_theme
        )

        sidebar_layout.addWidget(
            self.theme_combo
        )

        logout = QPushButton(
            "↪  Выйти"
        )

        logout.clicked.connect(
            self.logout
        )

        sidebar_layout.addWidget(
            logout
        )

        root.addWidget(
            sidebar
        )

        content = QVBoxLayout()

        content.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        toolbar = QHBoxLayout()

        back = QPushButton(
            "←"
        )

        back.setFixedWidth(
            42
        )

        forward = QPushButton(
            "→"
        )

        forward.setFixedWidth(
            42
        )

        refresh = QPushButton(
            "⟳"
        )

        refresh.setFixedWidth(
            42
        )

        home = QPushButton(
            "⌂"
        )

        home.setFixedWidth(
            42
        )

        self.address = QLineEdit()

        self.address.setPlaceholderText(
            "Поиск или адрес..."
        )

        toolbar.addWidget(
            back
        )

        toolbar.addWidget(
            forward
        )

        toolbar.addWidget(
            refresh
        )

        toolbar.addWidget(
            home
        )

        toolbar.addWidget(
            self.address
        )

        content.addLayout(
            toolbar
        )

        self.content_layout = content

        content.addWidget(
            self.home_page
        )

        root.addLayout(
            content
        )

        back.clicked.connect(
            self.browser.back
        )

        forward.clicked.connect(
            self.browser.forward
        )

        refresh.clicked.connect(
            self.browser.reload
        )

        home.clicked.connect(
            self.show_home
        )

        self.address.returnPressed.connect(
            self.navigate
        )

        self.browser.urlChanged.connect(
            self.url_changed
        )

    def apply_theme(self):
        QApplication.instance().setStyleSheet(
            theme_styles(
                self.current_theme
            )
        )

    def change_theme(self, theme):
        if theme not in THEMES:
            return

        self.current_theme = theme

        self.config["theme"] = theme

        save_config(
            self.config
        )

        self.apply_theme()

    def clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)

            widget = item.widget()

            if widget:
                widget.setParent(None)

    def show_home(self):
        self.clear_content()

        self.content_layout.addLayout(
            self.toolbar_layout()
        )

        self.content_layout.addWidget(
            self.home_page
        )

        self.address.clear()

    def toolbar_layout(self):
        toolbar = QHBoxLayout()

        return toolbar

    def new_tab(self):
        self.show_home()

    def open_url(self, url):
        self.clear_content()

        toolbar = QHBoxLayout()

        back = QPushButton("←")
        back.setFixedWidth(42)

        forward = QPushButton("→")
        forward.setFixedWidth(42)

        refresh = QPushButton("⟳")
        refresh.setFixedWidth(42)

        home = QPushButton("⌂")
        home.setFixedWidth(42)

        back.clicked.connect(
            self.browser.back
        )

        forward.clicked.connect(
            self.browser.forward
        )

        refresh.clicked.connect(
            self.browser.reload
        )

        home.clicked.connect(
            self.show_home
        )

        toolbar.addWidget(
            back
        )

        toolbar.addWidget(
            forward
        )

        toolbar.addWidget(
            refresh
        )

        toolbar.addWidget(
            home
        )

        toolbar.addWidget(
            self.address
        )

        self.content_layout.addLayout(
            toolbar
        )

        self.content_layout.addWidget(
            self.browser
        )

        self.browser.setUrl(
            QUrl(url)
        )

    def navigate(self):
        text = self.address.text().strip()

        if not text:
            return

        if text.startswith(
            "http://"
        ) or text.startswith(
            "https://"
        ):
            url = text

        elif "." in text and " " not in text:
            url = f"https://{text}"

        else:
            url = (
                "https://www.google.com/search?q="
                + requests.utils.quote(text)
            )

        self.open_url(
            url
        )

    def url_changed(self, url):
        self.address.setText(
            url.toString()
        )

    def open_profile(self):
        dialog = ProfileDialog(
            self
        )

        dialog.exec()

    def open_studio(self):
        QMessageBox.information(
            self,
            "Orbit Studio",
            (
                "Orbit Studio — настройка интерфейса.\n\n"
                "Темы уже доступны слева.\n"
                "Полный редактор UI добавим следующим этапом."
            ),
        )

    def open_vpn(self):
        QMessageBox.information(
            self,
            "Orbit VPN",
            (
                "Orbit VPN\n\n"
                "Здесь будет подключение к VPN-серверам."
            ),
        )

    def open_workspaces(self):
        QMessageBox.information(
            self,
            "Workspaces",
            (
                "Workspaces\n\n"
                "Здесь будут рабочие пространства "
                "Gaming / Work / Coding / Personal."
            ),
        )

    def open_notes(self):
        QMessageBox.information(
            self,
            "Notes",
            (
                "Orbit Notes\n\n"
                "Система заметок Orbit будет здесь."
            ),
        )

    def logout(self):
        try:
            post_api(
                self.api_url,
                "/api/auth/logout",
                {},
                token=self.token,
            )
        except Exception:
            pass

        clear_session()
        self.close()


# ============================================================
# API CHECK
# ============================================================

def check_api(api_url):
    try:
        response = requests.get(
            f"{api_url}/health",
            timeout=15,
        )

        return (
            response.status_code == 200
        )

    except Exception:
        return False


# ============================================================
# MAIN
# ============================================================

def main():
    create_directories()

    config = load_config()

    api_url = API_URL

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        APP_NAME
    )

    print(
        "Welcome to Orbit Browser"
    )

    if not check_api(
        api_url
    ):
        QMessageBox.warning(
            None,
            "Orbit API",
            (
                "Orbit API недоступен.\n\n"
                f"{api_url}"
            ),
        )

    saved_session = load_saved_session(
        api_url
    )

    if saved_session:
        window = MainWindow(
            api_url,
            saved_session,
            config,
        )

        window.show()

        sys.exit(
            app.exec()
        )

    auth = AuthWindow(
        api_url
    )

    if (
        auth.exec()
        != QDialog.DialogCode.Accepted
    ):
        sys.exit(0)

    window = MainWindow(
        api_url,
        auth.session,
        config,
    )

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()