import json
import os
import sys
from urllib.parse import quote

import requests

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QAction
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from orbit_pages import (
    BookmarksPage,
    DownloadsPage,
    HistoryPage,
    HomePage,
    NotesPage,
    ProfilePage,
    SettingsPage,
)
from orbit_storage import load_config, save_config
from orbit_ui import THEMES, site_theme_css, stylesheet

APP_NAME = "Orbit Browser"
APP_VERSION = "0.8.0"
API_URL = "https://orbit-api-9uqa.onrender.com"
SESSION_FILE = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "OrbitBrowser",
    "data",
    "session.json",
)


def check_api():
    try:
        return requests.get(f"{API_URL}/health", timeout=10).status_code == 200
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


class BrowserPage(QWebEnginePage):
    def __init__(self, profile, window, parent=None):
        super().__init__(profile, parent)
        self.orbit_window = window


class BrowserView(QWebEngineView):
    def __init__(self, window, profile, parent=None):
        super().__init__(parent)
        self.orbit_window = window
        self.setPage(BrowserPage(profile, window, self))
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        self.loadFinished.connect(self._after_load)

    def _after_load(self, ok):
        if ok:
            self.orbit_window.apply_site_theme(self)


class OrbitBrowser(QMainWindow):
    def __init__(self, session, config):
        super().__init__()
        self.token = session["token"]
        self.user = session["user"]
        self.config = config
        self.current_theme = config.get("theme", "VOID")
        self.web_profile = QWebEngineProfile.defaultProfile()
        self.web_profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        self.setWindowTitle("Orbit Browser")
        self.resize(1450, 900)
        self.build_ui()
        self.apply_theme()
        self.start_update_timer()
        self.show_home()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(5)

        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("toolbar")
        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(4, 2, 4, 2)
        toolbar.setSpacing(3)

        self.back_button = QPushButton("←")
        self.forward_button = QPushButton("→")
        self.reload_button = QPushButton("⟳")
        self.home_button = QPushButton("⌂")
        self.new_tab_button = QPushButton("+")
        self.menu_button = QPushButton("⋮")
        self.profile_button = QPushButton(
            self.user.get("display_name") or self.user.get("username", "Profile")
        )

        for button in (
            self.back_button,
            self.forward_button,
            self.reload_button,
            self.home_button,
            self.new_tab_button,
            self.menu_button,
        ):
            button.setFixedWidth(36)

        self.address = QLineEdit()
        self.address.setObjectName("address")
        self.address.setPlaceholderText("Поиск или адрес…")

        toolbar.addWidget(self.back_button)
        toolbar.addWidget(self.forward_button)
        toolbar.addWidget(self.reload_button)
        toolbar.addWidget(self.home_button)
        toolbar.addWidget(self.address, 1)
        toolbar.addWidget(self.new_tab_button)
        toolbar.addWidget(self.profile_button)
        toolbar.addWidget(self.menu_button)

        root.addWidget(toolbar_frame)

        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.home_page = HomePage(self)
        self.browser_tabs = QTabWidget()
        self.browser_tabs.setTabsClosable(True)
        self.browser_tabs.tabCloseRequested.connect(self.close_tab)
        self.browser_tabs.currentChanged.connect(self.sync_address)

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.browser_tabs)

        self.back_button.clicked.connect(self.go_back)
        self.forward_button.clicked.connect(self.go_forward)
        self.reload_button.clicked.connect(self.reload_page)
        self.home_button.clicked.connect(self.show_home)
        self.new_tab_button.clicked.connect(self.new_browser_tab)
        self.profile_button.clicked.connect(self.open_profile)
        self.menu_button.clicked.connect(self.open_menu)
        self.address.returnPressed.connect(self.navigate)

    def show_home(self):
        self.stack.setCurrentWidget(self.home_page)
        self.address.clear()
        self.home_page = HomePage(self)
        old = self.stack.widget(0)
        self.stack.removeWidget(old)
        old.deleteLater()
        self.stack.insertWidget(0, self.home_page)
        self.stack.setCurrentIndex(0)

    def show_browser(self):
        self.stack.setCurrentWidget(self.browser_tabs)

    def apply_theme(self):
        QApplication.instance().setStyleSheet(stylesheet(self.current_theme))

    def change_theme(self, theme):
        if theme not in THEMES:
            return
        self.current_theme = theme
        self.config["theme"] = theme
        save_config(self.config)
        self.apply_theme()
        self.apply_site_theme_to_all()

    def create_browser_tab(self, url=None):
        browser = BrowserView(self, self.web_profile)
        browser.urlChanged.connect(lambda value, b=browser: self.browser_url_changed(b, value))
        browser.titleChanged.connect(lambda title, b=browser: self.browser_title_changed(b, title))
        browser.setUrl(QUrl(url or "about:blank"))
        index = self.browser_tabs.addTab(browser, "Новая вкладка")
        self.browser_tabs.setCurrentIndex(index)
        self.show_browser()
        return browser

    def new_browser_tab(self):
        return self.create_browser_tab()

    def current_browser(self):
        widget = self.browser_tabs.currentWidget()
        return widget if isinstance(widget, QWebEngineView) else None

    def close_tab(self, index):
        if self.browser_tabs.count() <= 1:
            self.show_home()
            return
        widget = self.browser_tabs.widget(index)
        self.browser_tabs.removeTab(index)
        widget.deleteLater()

    def browser_title_changed(self, browser, title):
        index = self.browser_tabs.indexOf(browser)
        if index < 0:
            return
        title = title.strip() or "Новая вкладка"
        self.browser_tabs.setTabText(index, title[:26] + ("..." if len(title) > 26 else ""))

    def browser_url_changed(self, browser, url):
        if browser is self.current_browser():
            self.address.setText(url.toString())

    def sync_address(self, _index):
        browser = self.current_browser()
        self.address.setText(browser.url().toString() if browser else "")

    def navigate(self):
        self.navigate_text(self.address.text().strip())

    def navigate_text(self, text):
        text = text.strip()
        if not text:
            return
        if text.startswith(("http://", "https://")):
            url = text
        elif "." in text and " " not in text:
            url = "https://" + text
        else:
            url = self.config.get("search_engine", "https://www.google.com/search?q=") + quote(text)
        browser = self.current_browser()
        if not browser:
            browser = self.create_browser_tab()
        browser.setUrl(QUrl(url))
        self.show_browser()

    def open_url(self, url):
        browser = self.current_browser()
        if not browser:
            browser = self.create_browser_tab()
        browser.setUrl(QUrl(url))
        self.show_browser()

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

    def open_internal_page(self, page, _title):
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

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
        self.open_internal_page(ProfilePage(self), "Профиль")

    def open_menu(self):
        menu = self.menuBar()
        menu.clear()
        orbit = menu.addMenu("Orbit")
        for title, callback in (
            ("Главная", self.show_home),
            ("История", self.open_history),
            ("Закладки", self.open_bookmarks),
            ("Загрузки", self.open_downloads),
            ("Notes", self.open_notes),
            ("Профиль", self.open_profile),
            ("Настройки", self.open_settings),
        ):
            action = QAction(title, self)
            action.triggered.connect(callback)
            orbit.addAction(action)
        orbit.addSeparator()
        theme_menu = orbit.addMenu("Тема")
        for theme in THEMES:
            action = QAction(theme, self)
            action.triggered.connect(lambda checked=False, value=theme: self.change_theme(value))
            theme_menu.addAction(action)
        menu.setVisible(True)

    def apply_site_theme(self, browser):
        if not self.config.get("site_theme_enabled", True):
            return
        if not isinstance(browser, BrowserView):
            return
        css = site_theme_css(self.current_theme)
        css_json = json.dumps(css)
        js = f"""
        (() => {{
            const id = 'orbit-theme-style';
            let style = document.getElementById(id);
            if (!style) {{
                style = document.createElement('style');
                style.id = id;
                (document.head || document.documentElement).appendChild(style);
            }}
            style.textContent = {css_json};
            document.documentElement.classList.add('orbit-theme-enabled');
        }})();
        """
        try:
            browser.page().runJavaScript(js)
        except Exception:
            pass

    def apply_site_theme_to_all(self):
        for index in range(self.browser_tabs.count()):
            widget = self.browser_tabs.widget(index)
            if isinstance(widget, BrowserView):
                self.apply_site_theme(widget)

    def start_update_timer(self):
        self.update_timer = QTimer(self)
        minutes = int(self.config.get("update_check_minutes", 30))
        self.update_timer.setInterval(max(5, minutes) * 60 * 1000)
        self.update_timer.timeout.connect(self.check_for_updates)
        self.update_timer.start()

    def check_for_updates(self):
        try:
            response = requests.get(f"{API_URL}/api/update/version", timeout=8)
            if response.status_code != 200:
                return
            data = response.json()
            latest = data.get("version")
            if latest and latest != APP_VERSION:
                QMessageBox.information(self, "Orbit Browser", f"Доступна новая версия Orbit: {latest}")
        except Exception:
            pass


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
        QMessageBox.warning(
            None,
            "Orbit Browser",
            "Сохранённая сессия не найдена.\n\nСначала войдите в Orbit.",
        )
        sys.exit(0)

    window = OrbitBrowser(session, config)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
