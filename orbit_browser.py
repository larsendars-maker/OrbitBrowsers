import json
import os
import re
import sys
from urllib.parse import quote

import requests
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QComboBox, QFrame, QHBoxLayout, QLineEdit, QMainWindow, QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget

from orbit_pages import HomePage, HistoryPage, BookmarksPage, NotesPage, DownloadsPage, SettingsPage, SearchPage
from orbit_storage import load_config, save_config
from orbit_ui import THEMES, stylesheet

APP_NAME = "Orbit Browser"
APP_VERSION = "1.0.0"
API_URL = "https://orbit-api-9uqa.onrender.com"
SESSION_FILE = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "OrbitBrowser", "data", "session.json")


def check_api():
    try:
        return requests.get(f"{API_URL}/health", timeout=10).status_code == 200
    except Exception:
        return False


def load_session():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        token = saved.get("token")
        if not token:
            return None
        r = requests.get(f"{API_URL}/api/auth/session", headers={"Authorization": f"Bearer {token}"}, timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
        if not data.get("ok") or not data.get("user"):
            return None
        return {"token": token, "user": data["user"]}
    except Exception:
        return None


class BrowserView(QWebEngineView):
    def __init__(self, profile, browser_window, parent=None):
        super().__init__(parent)
        self.browser_window = browser_window
        self.setPage(QWebEnginePage(profile, self))
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        self.loadFinished.connect(self.apply_site_theme)

    def apply_site_theme(self):
        if not self.browser_window.config.get("site_theming", True):
            return
        theme = THEMES.get(self.browser_window.current_theme, THEMES["VOID"])
        css = f"""
        html, body {{
            background: {theme['bg']} !important;
            color: {theme['text']} !important;
        }}
        input, textarea, select {{
            background: {theme['surface']} !important;
            color: {theme['text']} !important;
            border-color: {theme['border']} !important;
        }}
        header, nav, aside, footer {{
            border-color: {theme['border']} !important;
        }}
        a {{ color: {theme['accent']} !important; }}
        """
        js = f"""
        (() => {{
            let old = document.getElementById('orbit-site-theme');
            if (old) old.remove();
            let s = document.createElement('style');
            s.id = 'orbit-site-theme';
            s.textContent = {json.dumps(css)};
            document.documentElement.appendChild(s);
        }})();
        """
        self.page().runJavaScript(js)


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
        self.resize(1480, 920)
        self.build_ui()
        self.apply_theme()
        self.open_home()
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(30 * 60 * 1000)
        self.update_timer.timeout.connect(self.check_updates)
        self.update_timer.start()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(7)

        chrome = QFrame()
        chrome.setObjectName("chromeBar")
        top = QHBoxLayout(chrome)
        top.setContentsMargins(7, 7, 7, 7)

        for text, fn in [("‹", self.go_back), ("›", self.go_forward), ("↻", self.reload_page), ("⌂", self.open_home)]:
            b = QPushButton(text)
            b.setFixedWidth(38)
            b.clicked.connect(fn)
            top.addWidget(b)

        self.address = QLineEdit()
        self.address.setPlaceholderText("Search Orbit or enter an address")
        self.address.returnPressed.connect(self.navigate)
        top.addWidget(self.address, 1)

        new_tab = QPushButton("+")
        new_tab.setFixedWidth(38)
        new_tab.clicked.connect(lambda: self.open_url("about:blank"))
        top.addWidget(new_tab)

        profile = QPushButton(self.user.get("display_name") or self.user.get("username", "Profile"))
        profile.clicked.connect(self.open_profile)
        top.addWidget(profile)

        menu = QPushButton("⋮")
        menu.setFixedWidth(38)
        menu.clicked.connect(self.open_menu)
        top.addWidget(menu)

        root.addWidget(chrome)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.sync_address)
        root.addWidget(self.tabs, 1)

    def apply_theme(self):
        QApplication.instance().setStyleSheet(stylesheet(self.current_theme))
        for i in range(self.tabs.count()):
            b = self.tabs.widget(i)
            if isinstance(b, BrowserView):
                b.apply_site_theme()

    def change_theme(self, theme):
        if theme not in THEMES:
            return
        self.current_theme = theme
        self.config["theme"] = theme
        save_config(self.config)
        self.apply_theme()

    def new_browser_tab(self, url=None):
        browser = BrowserView(self.web_profile, self)
        browser.urlChanged.connect(lambda u, b=browser: self.browser_url_changed(b, u))
        browser.titleChanged.connect(lambda t, b=browser: self.browser_title_changed(b, t))
        browser.setUrl(QUrl(url or "about:blank"))
        i = self.tabs.addTab(browser, "New Tab")
        self.tabs.setCurrentIndex(i)
        return browser

    def current_browser(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, QWebEngineView) else None

    def close_tab(self, index):
        if self.tabs.count() <= 1:
            self.open_home()
            return
        w = self.tabs.widget(index)
        self.tabs.removeTab(index)
        w.deleteLater()

    def browser_title_changed(self, browser, title):
        i = self.tabs.indexOf(browser)
        if i < 0:
            return
        title = title.strip() or "New Tab"
        self.tabs.setTabText(i, title[:22] + ("…" if len(title) > 22 else ""))

    def browser_url_changed(self, browser, url):
        if browser is self.current_browser():
            self.address.setText(url.toString())

    def sync_address(self, index):
        browser = self.current_browser()
        self.address.setText(browser.url().toString() if browser else "")

    def navigate(self):
        text = self.address.text().strip()
        if not text:
            return
        self.navigate_text(text)

    def navigate_text(self, text):
        text = text.strip()
        if text.startswith(("http://", "https://")):
            self.open_url(text)
        elif "." in text and " " not in text:
            self.open_url("https://" + text)
        else:
            self.open_orbit_search(text)

    def open_orbit_search(self, query=""):
        page = SearchPage(self, query)
        i = self.tabs.addTab(page, "Orbit Search")
        self.tabs.setCurrentIndex(i)
        self.address.setText(f"orbit://search?q={quote(query)}" if query else "orbit://search")

    def open_url(self, url):
        if url.startswith("orbit://search"):
            q = ""
            if "?q=" in url:
                q = url.split("?q=", 1)[1]
            self.open_orbit_search(q)
            return
        browser = self.current_browser()
        if not browser:
            browser = self.new_browser_tab(url)
        else:
            browser.setUrl(QUrl(url))

    def open_home(self):
        if self.tabs.count() and isinstance(self.tabs.currentWidget(), HomePage):
            return
        page = HomePage(self)
        i = self.tabs.addTab(page, "Orbit")
        self.tabs.setCurrentIndex(i)
        self.address.clear()

    def go_back(self):
        b = self.current_browser()
        if b:
            b.back()

    def go_forward(self):
        b = self.current_browser()
        if b:
            b.forward()

    def reload_page(self):
        b = self.current_browser()
        if b:
            b.reload()

    def open_internal_page(self, page, title):
        i = self.tabs.addTab(page, title)
        self.tabs.setCurrentIndex(i)
        self.address.setText(f"orbit://{title.lower()}")

    def open_history(self):
        self.open_internal_page(HistoryPage(self), "History")

    def open_bookmarks(self):
        self.open_internal_page(BookmarksPage(self), "Bookmarks")

    def open_notes(self):
        self.open_internal_page(NotesPage(self), "Notes")

    def open_downloads(self):
        self.open_internal_page(DownloadsPage(self), "Downloads")

    def open_settings(self):
        self.open_internal_page(SettingsPage(self), "Settings")

    def open_profile(self):
        name = self.user.get("display_name") or self.user.get("username", "User")
        xp = int(self.user.get("xp", 0))
        level = xp // 500 + 1
        role = self.user.get("role", "user")
        title = "Founder • Creator of Orbit" if role == "founder" else self.user.get("title", "Explorer")
        QMessageBox.information(self, "Orbit Profile", f"{name}\n\n{title}\nLevel {level}\n{xp} XP")

    def open_menu(self):
        bar = self.menuBar()
        bar.clear()
        m = bar.addMenu("Orbit")
        for text, fn in [("History", self.open_history), ("Bookmarks", self.open_bookmarks), ("Downloads", self.open_downloads), ("Notes", self.open_notes), ("Settings", self.open_settings)]:
            a = QAction(text, self)
            a.triggered.connect(fn)
            m.addAction(a)
        bar.setVisible(True)

    def check_updates(self):
        return


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
