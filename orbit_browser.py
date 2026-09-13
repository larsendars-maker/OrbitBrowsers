
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import requests

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView


# ============================================================
# ORBIT CONFIG
# ============================================================

APP_NAME = "OrbitBrowser"

API_URL = "https://orbit-api-9uqa.onrender.com"

APP_DIR = Path(
    os.environ.get(
        "LOCALAPPDATA",
        Path.home() / "AppData" / "Local",
    )
) / APP_NAME

DATA_DIR = APP_DIR / "data"
CONFIG_DIR = APP_DIR / "config"
PROFILE_DIR = APP_DIR / "profiles"
THEME_DIR = APP_DIR / "themes"
NOTE_DIR = APP_DIR / "notes"
WORKSPACE_DIR = APP_DIR / "workspaces"
DOWNLOAD_DIR = APP_DIR / "downloads"
CACHE_DIR = APP_DIR / "cache"
LOG_DIR = APP_DIR / "logs"
BACKUP_DIR = APP_DIR / "backups"

CONFIG_FILE = CONFIG_DIR / "config.json"
SESSION_FILE = DATA_DIR / "session.json"


# ============================================================
# DIRECTORIES
# ============================================================

def ensure_directories():
    folders = [
        APP_DIR,
        DATA_DIR,
        CONFIG_DIR,
        PROFILE_DIR,
        THEME_DIR,
        NOTE_DIR,
        WORKSPACE_DIR,
        DOWNLOAD_DIR,
        CACHE_DIR,
        LOG_DIR,
        BACKUP_DIR,
    ]

    for folder in folders:
        folder.mkdir(
            parents=True,
            exist_ok=True,
        )


# ============================================================
# CONFIG
# ============================================================

def load_config():
    ensure_directories()

    if not CONFIG_FILE.exists():

        config = {
            "api_url": API_URL,
            "theme": "VOID",
            "search_engine": "https://www.google.com/search?q=",
        }

        CONFIG_FILE.write_text(
            json.dumps(
                config,
                ensure_ascii=False,
                indent=4,
            ),
            encoding="utf-8",
        )

        return config

    try:

        return json.loads(
            CONFIG_FILE.read_text(
                encoding="utf-8",
            )
        )

    except Exception:

        return {
            "api_url": API_URL,
            "theme": "VOID",
            "search_engine": "https://www.google.com/search?q=",
        }


# ============================================================
# SESSION
# ============================================================

def save_session(token, user):

    ensure_directories()

    SESSION_FILE.write_text(
        json.dumps(
            {
                "token": token,
                "user": user,
            },
            ensure_ascii=False,
            indent=4,
        ),
        encoding="utf-8",
    )


def clear_session():

    try:
        SESSION_FILE.unlink(
            missing_ok=True
        )
    except Exception:
        pass


def load_saved_session(api_url):

    if not SESSION_FILE.exists():
        return None

    try:

        data = json.loads(
            SESSION_FILE.read_text(
                encoding="utf-8",
            )
        )

        token = data.get("token")

        if not token:
            clear_session()
            return None

        response = requests.get(
            f"{api_url.rstrip('/')}/api/auth/session",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=15,
        )

        if not response.ok:
            clear_session()
            return None

        result = response.json()

        user = result.get("user")

        if not user:
            clear_session()
            return None

        # Сохраняем актуальные данные пользователя.
        save_session(
            token,
            user,
        )

        return {
            "token": token,
            "user": user,
        }

    except (
        requests.RequestException,
        json.JSONDecodeError,
        KeyError,
        OSError,
    ):
        return None


# ============================================================
# THEMES
# ============================================================

THEMES = {

    "VOID": {
        "background": "#080a0f",
        "surface": "#11151d",
        "surface2": "#171c26",
        "border": "#252c38",
        "text": "#f4f7fb",
        "muted": "#8d97a8",
        "accent": "#7c5cff",
    },

    "BLUE": {
        "background": "#071019",
        "surface": "#0d1824",
        "surface2": "#132130",
        "border": "#223446",
        "text": "#edf6ff",
        "muted": "#8ea5ba",
        "accent": "#3f9cff",
    },

    "EMERALD": {
        "background": "#06100c",
        "surface": "#0b1913",
        "surface2": "#12241b",
        "border": "#223a2e",
        "text": "#edfff5",
        "muted": "#8eae9d",
        "accent": "#39dd94",
    },

    "SUNSET": {
        "background": "#13090d",
        "surface": "#211017",
        "surface2": "#2c1620",
        "border": "#43222d",
        "text": "#fff1f0",
        "muted": "#c29ca1",
        "accent": "#ff6488",
    },
}


def build_stylesheet(theme_name):

    theme = THEMES.get(
        theme_name,
        THEMES["VOID"],
    )

    return f"""
    * {{
        font-family: "Segoe UI";
    }}

    QMainWindow {{
        background: {theme["background"]};
        color: {theme["text"]};
    }}

    QWidget {{
        color: {theme["text"]};
    }}

    QToolBar {{
        background: {theme["surface"]};
        border: none;
        padding: 8px;
        spacing: 6px;
    }}

    QToolButton {{
        background: transparent;
        color: {theme["muted"]};
        border: none;
        border-radius: 9px;
        padding: 8px 11px;
        font-size: 11pt;
    }}

    QToolButton:hover {{
        background: {theme["surface2"]};
        color: {theme["text"]};
    }}

    QPushButton {{
        background: {theme["surface2"]};
        color: {theme["text"]};
        border: 1px solid {theme["border"]};
        border-radius: 10px;
        padding: 9px 14px;
    }}

    QPushButton:hover {{
        background: {theme["accent"]};
        border-color: {theme["accent"]};
        color: white;
    }}

    QLineEdit {{
        background: {theme["surface2"]};
        color: {theme["text"]};
        border: 1px solid {theme["border"]};
        border-radius: 13px;
        padding: 11px 14px;
        selection-background-color: {theme["accent"]};
        font-size: 10.5pt;
    }}

    QLineEdit:focus {{
        border: 1px solid {theme["accent"]};
    }}

    QTabWidget::pane {{
        border: none;
        background: {theme["background"]};
    }}

    QTabBar {{
        background: {theme["surface"]};
    }}

    QTabBar::tab {{
        background: {theme["surface"]};
        color: {theme["muted"]};
        border: none;
        padding: 10px 18px;
        margin-right: 3px;
        border-radius: 11px 11px 0 0;
    }}

    QTabBar::tab:selected {{
        background: {theme["surface2"]};
        color: {theme["text"]};
    }}

    QTabBar::tab:hover {{
        background: {theme["surface2"]};
        color: {theme["text"]};
    }}

    QStatusBar {{
        background: {theme["surface"]};
        color: {theme["muted"]};
        border-top: 1px solid {theme["border"]};
    }}

    QFrame#card {{
        background: {theme["surface"]};
        border: 1px solid {theme["border"]};
        border-radius: 18px;
    }}

    QFrame#hero {{
        background: {theme["surface"]};
        border: 1px solid {theme["border"]};
        border-radius: 24px;
    }}
    """


# ============================================================
# LOGIN / REGISTER
# ============================================================

class AuthWindow(QDialog):

    def __init__(self, api_url, parent=None):

        super().__init__(parent)

        self.api_url = api_url.rstrip("/")
        self.token = None
        self.user = None

        self.setWindowTitle(
            "Orbit Account"
        )

        self.setFixedSize(
            470,
            610,
        )

        self.setStyleSheet(
            build_stylesheet("VOID")
        )

        self.build_ui()

    def build_ui(self):

        root = QVBoxLayout(self)

        root.setContentsMargins(
            38,
            38,
            38,
            38,
        )

        root.setSpacing(12)

        logo = QLabel("ORBIT")

        logo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        logo.setFont(
            QFont(
                "Segoe UI",
                30,
                QFont.Weight.Bold,
            )
        )

        root.addWidget(logo)

        subtitle = QLabel(
            "Войди в свою Orbit Account"
        )

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        subtitle.setStyleSheet(
            "color: #8d97a8;"
        )

        root.addWidget(subtitle)

        root.addSpacing(22)

        self.username = QLineEdit()

        self.username.setPlaceholderText(
            "Имя пользователя"
        )

        self.email = QLineEdit()

        self.email.setPlaceholderText(
            "Email"
        )

        self.password = QLineEdit()

        self.password.setPlaceholderText(
            "Пароль"
        )

        self.password.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        root.addWidget(
            self.username
        )

        root.addWidget(
            self.email
        )

        root.addWidget(
            self.password
        )

        root.addSpacing(8)

        login_button = QPushButton(
            "Войти"
        )

        login_button.clicked.connect(
            self.login
        )

        register_button = QPushButton(
            "Создать аккаунт"
        )

        register_button.clicked.connect(
            self.register
        )

        root.addWidget(
            login_button
        )

        root.addWidget(
            register_button
        )

        self.status = QLabel()

        self.status.setWordWrap(True)

        self.status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status.setStyleSheet(
            "color: #ff8294; padding: 12px;"
        )

        root.addWidget(
            self.status
        )

        root.addStretch()

        api_label = QLabel(
            self.api_url
        )

        api_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        api_label.setStyleSheet(
            "color: #5f6b7d; font-size: 8pt;"
        )

        root.addWidget(
            api_label
        )

    def register(self):

        username = self.username.text().strip()
        email = self.email.text().strip()
        password = self.password.text()

        if len(username) < 3:
            self.status.setText(
                "Имя пользователя: минимум 3 символа."
            )
            return

        if not email:
            self.status.setText(
                "Введите email."
            )
            return

        if len(password) < 6:
            self.status.setText(
                "Пароль: минимум 6 символов."
            )
            return

        try:

            response = requests.post(
                f"{self.api_url}/api/auth/register",
                json={
                    "username": username,
                    "email": email,
                    "password": password,
                },
                timeout=20,
            )

            data = response.json()

            if response.ok:

                self.token = data["token"]
                self.user = data["user"]

                save_session(
                    self.token,
                    self.user,
                )

                self.accept()
                return

            self.status.setText(
                data.get(
                    "detail",
                    "Не удалось создать аккаунт.",
                )
            )

        except requests.RequestException as error:

            self.status.setText(
                "Не удалось подключиться к серверу.\n"
                f"{error}"
            )

    def login(self):

        email = self.email.text().strip()
        password = self.password.text()

        if not email:
            self.status.setText(
                "Введите email."
            )
            return

        if not password:
            self.status.setText(
                "Введите пароль."
            )
            return

        try:

            response = requests.post(
                f"{self.api_url}/api/auth/login",
                json={
                    "email": email,
                    "password": password,
                },
                timeout=20,
            )

            data = response.json()

            if response.ok:

                self.token = data["token"]
                self.user = data["user"]

                save_session(
                    self.token,
                    self.user,
                )

                self.accept()
                return

            self.status.setText(
                data.get(
                    "detail",
                    "Неверный email или пароль.",
                )
            )

        except requests.RequestException as error:

            self.status.setText(
                "Не удалось подключиться к серверу.\n"
                f"{error}"
            )


# ============================================================
# HOME PAGE
# ============================================================

class HomePage(QWidget):

    def __init__(self, browser):

        super().__init__()

        self.browser = browser

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            80,
            70,
            80,
            70,
        )

        layout.setSpacing(22)

        hero = QFrame()

        hero.setObjectName(
            "hero"
        )

        hero_layout = QVBoxLayout(
            hero
        )

        hero_layout.setContentsMargins(
            42,
            42,
            42,
            42,
        )

        logo = QLabel("ORBIT")

        logo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        logo.setFont(
            QFont(
                "Segoe UI",
                38,
                QFont.Weight.Bold,
            )
        )

        hero_layout.addWidget(
            logo
        )

        subtitle = QLabel(
            "Твой браузер. "
            "Твои профили. "
            "Твоё пространство."
        )

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        subtitle.setStyleSheet(
            "color: #8d97a8; font-size: 12pt;"
        )

        hero_layout.addWidget(
            subtitle
        )

        hero_layout.addSpacing(
            14
        )

        self.search = QLineEdit()

        self.search.setPlaceholderText(
            "Поиск или адрес сайта..."
        )

        self.search.returnPressed.connect(
            self.search_web
        )

        hero_layout.addWidget(
            self.search
        )

        layout.addWidget(
            hero
        )

        cards = QHBoxLayout()

        cards.addWidget(
            self.make_card(
                "● ПРОФИЛЬ",
                self.browser.username,
                "Текущий аккаунт",
            )
        )

        cards.addWidget(
            self.make_card(
                "◆ VPN",
                "Отключён",
                "Подключение будет здесь",
            )
        )

        cards.addWidget(
            self.make_card(
                "✦ STUDIO",
                "Orbit Studio",
                "Настройка внешнего вида",
            )
        )

        layout.addLayout(
            cards
        )

        layout.addStretch()

    def make_card(
        self,
        title,
        value,
        description,
    ):

        card = QFrame()

        card.setObjectName(
            "card"
        )

        layout = QVBoxLayout(
            card
        )

        layout.setContentsMargins(
            22,
            20,
            22,
            20,
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            "color: #8d97a8;"
        )

        value_label = QLabel(
            value
        )

        value_label.setFont(
            QFont(
                "Segoe UI",
                15,
                QFont.Weight.Bold,
            )
        )

        description_label = QLabel(
            description
        )

        description_label.setStyleSheet(
            "color: #687284;"
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        layout.addWidget(
            description_label
        )

        return card

    def search_web(self):

        text = self.search.text().strip()

        if text:
            self.browser.open_text(
                text
            )


# ============================================================
# BROWSER TAB
# ============================================================

class BrowserTab(QWebEngineView):

    def __init__(self):

        super().__init__()

        settings = self.settings()

        settings.setAttribute(
            settings.WebAttribute.JavascriptEnabled,
            True,
        )

        settings.setAttribute(
            settings.WebAttribute.LocalStorageEnabled,
            True,
        )

        settings.setAttribute(
            settings.WebAttribute.FullScreenSupportEnabled,
            True,
        )

        self.setUrl(
            QUrl("about:blank")
        )


# ============================================================
# MAIN BROWSER
# ============================================================

class OrbitBrowser(QMainWindow):

    def __init__(
        self,
        user,
        config,
        token,
    ):

        super().__init__()

        self.user = user
        self.config = config
        self.token = token

        self.username = user.get(
            "username",
            "Orbit User",
        )

        self.setWindowTitle(
            f"Orbit Browser — {self.username}"
        )

        self.resize(
            1500,
            920,
        )

        self.setMinimumSize(
            1100,
            700,
        )

        self.setStyleSheet(
            build_stylesheet(
                config.get(
                    "theme",
                    "VOID",
                )
            )
        )

        self.tabs = QTabWidget()

        self.tabs.setTabsClosable(
            True
        )

        self.tabs.setMovable(
            True
        )

        self.tabs.tabCloseRequested.connect(
            self.close_tab
        )

        self.tabs.currentChanged.connect(
            self.tab_changed
        )

        self.setCentralWidget(
            self.tabs
        )

        self.create_toolbar()

        self.create_home_tab()

        self.statusBar().showMessage(
            f"Выполнен вход: {self.username}"
        )

    # --------------------------------------------------------
    # TOOLBAR
    # --------------------------------------------------------

    def create_toolbar(self):

        toolbar = QToolBar()

        toolbar.setMovable(
            False
        )

        self.addToolBar(
            toolbar
        )

        self.add_button(
            toolbar,
            "←",
            self.go_back,
            "Назад",
        )

        self.add_button(
            toolbar,
            "→",
            self.go_forward,
            "Вперёд",
        )

        self.add_button(
            toolbar,
            "⟳",
            self.reload_page,
            "Обновить",
        )

        self.add_button(
            toolbar,
            "⌂",
            self.open_home,
            "Домой",
        )

        self.address = QLineEdit()

        self.address.setPlaceholderText(
            "Введите адрес или поисковый запрос..."
        )

        self.address.returnPressed.connect(
            self.navigate
        )

        toolbar.addWidget(
            self.address
        )

        self.add_button(
            toolbar,
            "+",
            self.create_browser_tab,
            "Новая вкладка",
        )

        self.add_button(
            toolbar,
            "✦",
            self.show_studio,
            "Orbit Studio",
        )

        self.add_button(
            toolbar,
            "●",
            self.show_profile,
            "Профиль",
        )

        self.add_button(
            toolbar,
            "↪",
            self.logout,
            "Выйти",
        )

    def add_button(
        self,
        toolbar,
        text,
        callback,
        tooltip,
    ):

        action = QAction(
            text,
            self,
        )

        action.setToolTip(
            tooltip
        )

        action.triggered.connect(
            callback
        )

        toolbar.addAction(
            action
        )

    # --------------------------------------------------------
    # HOME
    # --------------------------------------------------------

    def create_home_tab(self):

        page = HomePage(
            self
        )

        index = self.tabs.addTab(
            page,
            "Orbit",
        )

        self.tabs.setCurrentIndex(
            index
        )

    def open_home(self):

        self.create_home_tab()

    # --------------------------------------------------------
    # BROWSER
    # --------------------------------------------------------

    def create_browser_tab(self):

        browser = BrowserTab()

        browser.urlChanged.connect(
            lambda url, view=browser:
            self.url_changed(
                view,
                url,
            )
        )

        browser.titleChanged.connect(
            lambda title, view=browser:
            self.title_changed(
                view,
                title,
            )
        )

        browser.iconChanged.connect(
            lambda icon, view=browser:
            self.icon_changed(
                view,
                icon,
            )
        )

        index = self.tabs.addTab(
            browser,
            "Новая вкладка",
        )

        self.tabs.setCurrentIndex(
            index
        )

    def current_browser(self):

        widget = self.tabs.currentWidget()

        if isinstance(
            widget,
            BrowserTab,
        ):
            return widget

        return None

    # --------------------------------------------------------
    # NAVIGATION
    # --------------------------------------------------------

    def navigate(self):

        browser = self.current_browser()

        if browser is None:

            self.create_browser_tab()

            browser = self.current_browser()

        text = self.address.text().strip()

        self.open_text(
            text,
            browser,
        )

    def open_text(
        self,
        text,
        browser=None,
    ):

        if not text:
            return

        if browser is None:
            browser = self.current_browser()

        if browser is None:

            self.create_browser_tab()

            browser = self.current_browser()

        if text.startswith(
            (
                "http://",
                "https://",
            )
        ):

            target = text

        elif "." in text and " " not in text:

            target = (
                "https://"
                + text
            )

        else:

            search_engine = self.config.get(
                "search_engine",
                "https://www.google.com/search?q=",
            )

            target = (
                search_engine
                + quote_plus(text)
            )

        browser.setUrl(
            QUrl(target)
        )

    def go_back(self):

        browser = self.current_browser()

        if browser:
            browser.back()

    def go_forward(self):

        browser = self.current_browser()

        if browser:
            browser.forward()

    def reload_page(self):

        browser = self.current_browser()

        if browser:
            browser.reload()

    # --------------------------------------------------------
    # TABS
    # --------------------------------------------------------

    def close_tab(self, index):

        if self.tabs.count() <= 1:
            return

        widget = self.tabs.widget(
            index
        )

        self.tabs.removeTab(
            index
        )

        widget.deleteLater()

    def tab_changed(self, index):

        widget = self.tabs.widget(
            index
        )

        if isinstance(
            widget,
            BrowserTab,
        ):

            self.address.setText(
                widget.url().toString()
            )

        else:

            self.address.clear()

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    def url_changed(
        self,
        browser,
        url,
    ):

        if browser is self.current_browser():

            self.address.setText(
                url.toString()
            )

    def title_changed(
        self,
        browser,
        title,
    ):

        index = self.tabs.indexOf(
            browser
        )

        if index < 0:
            return

        title = (
            title.strip()
            or "Новая вкладка"
        )

        self.tabs.setTabText(
            index,
            title[:28],
        )

        if browser is self.current_browser():

            self.statusBar().showMessage(
                f"{title} • {self.username}"
            )

    def icon_changed(
        self,
        browser,
        icon,
    ):

        index = self.tabs.indexOf(
            browser
        )

        if index >= 0 and not icon.isNull():

            self.tabs.setTabIcon(
                index,
                icon,
            )

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    def show_profile(self):

        QMessageBox.information(
            self,
            "Orbit Profile",
            f"Пользователь:\n"
            f"{self.username}\n\n"
            f"Email:\n"
            f"{self.user.get('email', '')}",
        )

    # --------------------------------------------------------
    # STUDIO
    # --------------------------------------------------------

    def show_studio(self):

        QMessageBox.information(
            self,
            "Orbit Studio",
            "Orbit Studio подключён.\n\n"
            "Следующий этап — полноценный "
            "редактор тем и интерфейса.",
        )

    # --------------------------------------------------------
    # LOGOUT
    # --------------------------------------------------------

    def logout(self):

        answer = QMessageBox.question(
            self,
            "Выход",
            "Выйти из Orbit Account?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:

            requests.post(
                f"{self.config.get('api_url', API_URL)}/api/auth/logout",
                headers={
                    "Authorization":
                    f"Bearer {self.token}"
                },
                timeout=10,
            )

        except requests.RequestException:
            pass

        clear_session()

        self.close()


# ============================================================
# START
# ============================================================

def main():

    ensure_directories()

    config = load_config()

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Orbit Browser"
    )

    app.setApplicationDisplayName(
        "Orbit Browser"
    )

    app.setOrganizationName(
        "Orbit"
    )

    api_url = config.get(
        "api_url",
        API_URL,
    )

    # ========================================================
    # AUTO LOGIN
    # ========================================================

    saved_session = load_saved_session(
        api_url
    )

    if saved_session:

        browser = OrbitBrowser(
            saved_session["user"],
            config,
            saved_session["token"],
        )

        browser.show()

        sys.exit(
            app.exec()
        )

    # ========================================================
    # LOGIN / REGISTER
    # ========================================================

    auth = AuthWindow(
        api_url
    )

    if auth.exec() != QDialog.DialogCode.Accepted:
        return

    browser = OrbitBrowser(
        auth.user,
        config,
        auth.token,
    )

    browser.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()

