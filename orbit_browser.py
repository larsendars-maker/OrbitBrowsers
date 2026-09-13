import json
import os
import sys
from urllib.parse import quote

import requests
from PySide6.QtCore import QUrl
from PySide6.QtGui import QAction
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QComboBox, QFrame, QHBoxLayout, QLineEdit, QMainWindow, QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget

from orbit_pages import HomePage, HistoryPage, BookmarksPage, NotesPage, DownloadsPage, SettingsPage
from orbit_storage import load_config, save_config
from orbit_ui import THEMES, stylesheet

APP_NAME = "Orbit Browser"
APP_VERSION = "0.5.0"
API_URL = "https://orbit-api-9uqa.onrender.com"
SESSION_FILE = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "OrbitBrowser", "data", "session.json")


def check_api():
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        return response.status_code == 200
    except Exception:
        return False


def load_session():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as file:
            saved = json.load(file)
        token = saved.get("token")
        if not token:
            return None
        response = requests.get(
            f"{API_URL}/api/auth/session",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if response.status_code != 200:
            return None
        data = response.json()
        if not data.get("ok") or not data.get("user"):
            return None
        session = {"token": token, "user": data["user"]}
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        with open(SESSION_FILE, "w", encoding="utf-8") as file:
            json.dump(session, file, ensure_ascii=False, indent=4)
        return session
    except Exception:
        return None


class BrowserView(QWebEngineView):
    def __init__(self, profile, parent=None):
        super().__init__(parent)
        self.setPage(QWebEnginePage(profile, self))
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)


class OrbitBrowser(QMainWindow):
    def __init__(self, session, config):
        super().__init__()
        self.token = session["token"]
        self.user = session["user"]
        self.config = config
        self.current_theme = config.get("theme", "VOID")
        self.web_profile = QWebEngineProfile.defaultProfile()
        self.web_profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        self.setWindowTitle("Orbit Browser")
        self.resize(1450, 900)
        self.build_ui()
        self.apply_theme()
        self.open_home()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(7)

        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("toolbar")
        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(8, 8, 8, 8)

        back = QPushButton("←")
        forward = QPushButton("→")
        reload_button = QPushButton("⟳")
        home = QPushButton("⌂")
        for button in (back, forward, reload_button, home):
            button.setFixedWidth(40)

        back.clicked.connect(self.go_back)
        forward.clicked.connect(self.go_forward)
        reload_button.clicked.connect(self.reload_page)
        home.clicked.connect(self.open_home)

        self.address = QLineEdit()
        self.address.setPlaceholderText("Поиск или адрес...")
        self.address.returnPressed.connect(self.navigate)

        new_tab = QPushButton("+")
        new_tab.setFixedWidth(40)
        new_tab.clicked.connect(self.new_browser_tab)

        profile_button = QPushButton(self.user.get("display_name", self.user.get("username", "Profile")))
        profile_button.clicked.connect(self.open_profile)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.setCurrentText(self.current_theme)
        self.theme_combo.currentTextChanged.connect(self.change_theme)

        menu = QPushButton("⋮")
        menu.setFixedWidth(40)
        menu.clicked.connect(self.open_menu)

        toolbar.addWidget(back)
        toolbar.addWidget(forward)
        toolbar.addWidget(reload_button)
        toolbar.addWidget(home)
        toolbar.addWidget(self.address, 1)
        toolbar.addWidget(new_tab)
        toolbar.addWidget(profile_button)
        toolbar.addWidget(self.theme_combo)
        toolbar.addWidget(menu)
        root.addWidget(toolbar_frame)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.sync_address)
        root.addWidget(self.tabs, 1)

    def apply_theme(self):
        QApplication.instance().setStyleSheet(stylesheet(self.current_theme))

    def change_theme(self, theme):
        if theme not in THEMES:
            return
        self.current_theme = theme
        self.config["theme"] = theme
        save_config(self.config)
        self.apply_theme()

    def new_browser_tab(self, url=None):
        browser = BrowserView(self.web_profile)
        browser.urlChanged.connect(lambda value, b=browser: self.browser_url_changed(b, value))
        browser.titleChanged.connect(lambda title, b=browser: self.browser_title_changed(b, title))
        browser.setUrl(QUrl(url or "about:blank"))
        index = self.tabs.addTab(browser, "Новая вкладка")
        self.tabs.setCurrentIndex(index)
        return browser

    def current_browser(self):
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, QWebEngineView) else None

    def close_tab(self, index):
        if self.tabs.count() <= 1:
            self.open_home()
            return
        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        widget.deleteLater()

    def browser_title_changed(self, browser, title):
        index = self.tabs.indexOf(browser)
        if index < 0:
            return
        title = title.strip() or "Новая вкладка"
        if len(title) > 25:
            title = title[:25] + "..."
        self.tabs.setTabText(index, title)

    def browser_url_changed(self, browser, url):
        if browser is self.current_browser():
            self.address.setText(url.toString())

    def sync_address(self, _index):
        browser = self.current_browser()
        self.address.setText(browser.url().toString() if browser else "")

    def navigate(self):
        self.navigate_text(self.address.text().strip())

    def navigate_text(self, text):
        if not text:
            return
        if text.startswith(("http://", "https://")):
            url = text
        elif "." in text and " " not in text:
            url = "https://" + text
        else:
            engine = self.config.get("search_engine", "https://www.google.com/search?q=")
            url = engine + quote(text)
        browser = self.current_browser() or self.new_browser_tab()
        browser.setUrl(QUrl(url))

    def open_url(self, url):
        browser = self.current_browser() or self.new_browser_tab()
        browser.setUrl(QUrl(url))

    def open_home(self):
        page = HomePage(self)
        index = self.tabs.addTab(page, "Orbit")
        self.tabs.setCurrentIndex(index)

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

    def open_internal_page(self, page, title):
        index = self.tabs.addTab(page, title)
        self.tabs.setCurrentIndex(index)

    def open_history(self):
        self.open_internal_page(HistoryPage(self), "История")

    def open_bookmarks(self):
        self.open_internal_page(BookmarksPage(self), "Закладки")

    def open_notes(self):
        self.open_internal_page(NotesPage(self), "Notes")

    def open_downloads(self):
        self.open_internal_page(DownloadsPage(self), "Загрузки")

    def open_settings(self):
        self.open_internal_page(SettingsPage(self), "Настройки")

    def open_profile(self):
        name = self.user.get("display_name", self.user.get("username", "User"))
        xp = int(self.user.get("xp", 0))
        level = (xp // 500) + 1
        role = self.user.get("role", "user")
        role_text = "Founder • Creator of Orbit" if role == "founder" else self.user.get("title", "Explorer")
        QMessageBox.information(self, "Orbit Profile", f"{name}\n\n{role_text}\nLevel {level}\n{xp} XP")

    def open_menu(self):
        menu_bar = self.menuBar()
        menu_bar.clear()
        orbit_menu = menu_bar.addMenu("Orbit")
        actions = [
            ("История", self.open_history),
            ("Закладки", self.open_bookmarks),
            ("Загрузки", self.open_downloads),
            ("Notes", self.open_notes),
            ("Настройки", self.open_settings),
        ]
        for title, callback in actions:
            action = QAction(title, self)
            action.triggered.connect(callback)
            orbit_menu.addAction(action)
        menu_bar.setVisible(True)


def main():
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    config = load_config()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyleSheet(stylesheet(config.get("theme", "VOID")))
    print("Welcome to Orbit Browser")

    if not check_api():
        QMessageBox.warning(None, "Orbit API", f"Orbit API недоступен.\n\n{API_URL}")

    session = load_session()
    if not session:
        QMessageBox.warning(None, "Orbit Browser", "Сохранённая сессия не найдена.\n\nСначала войдите в Orbit.")
        sys.exit(0)

    window = OrbitBrowser(session, config)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
