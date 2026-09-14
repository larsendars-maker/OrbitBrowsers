import json
import os
import sys
import shutil
import tempfile
import subprocess
from urllib.parse import quote

import requests
from PySide6.QtCore import QUrl, QTimer, Qt, QStandardPaths, QSize, Signal
from PySide6.QtGui import QAction, QPixmap, QIcon, QKeySequence, QShortcut
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget, QSplashScreen, QProgressDialog, QFileDialog, QMenu, QStyle, QTabBar

from orbit_pages import HomePage, HistoryPage, BookmarksPage, NotesPage, DownloadsPage, SettingsPage, SearchPage, DiagnosticsPage, ProfilePage, GeminiPage, SupportPage, AdminPanelPage
from orbit_storage import load_config, save_config, load_local_profile, save_local_profile, add_history, add_download
from orbit_ui import THEMES, stylesheet, tr

APP_NAME = "Orbit Browser"
APP_VERSION = "1.16.15"
API_URL = "https://orbit-api-9uqa.onrender.com"
GITHUB_REPO = "larsendars-maker/OrbitBrowsers"
WINDOWS_APP_USER_MODEL_ID = "Larsenda.OrbitBrowser"


def configure_windows_identity():
    """Задаёт стабильный Windows AppUserModelID, чтобы Orbit использовал свою иконку и в панели задач."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(WINDOWS_APP_USER_MODEL_ID)
    except Exception:
        pass


def resource_path(*relative_parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *relative_parts)

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
        url = self.url().toString().lower()
        search_hosts = ("google.", "bing.com", "duckduckgo.com", "accounts.google.", "login.microsoftonline.com")
        if any(host in url for host in search_hosts):
            self.page().runJavaScript("document.getElementById('orbit-site-theme')?.remove();")
            return
        if not self.browser_window.config.get("site_theming", True):
            return
        t = THEMES.get(self.browser_window.current_theme, THEMES["VOID"])
        css = f"""
        :root {{ color-scheme: dark !important; }}
        html, body {{ background: {t['bg']} !important; color: {t['text']} !important; }}
        body, main, section, article, header, footer, nav, aside, dialog {{ background-color: {t['bg']} !important; color: {t['text']} !important; }}
        input, textarea, select {{ background: {t['surface']} !important; color: {t['text']} !important; border-color: {t['border']} !important; }}
        a {{ color: {t['accent']} !important; }}
        """
        js = f"""
        (() => {{
            let old = document.getElementById('orbit-site-theme');
            if (old) old.remove();
            let style = document.createElement('style');
            style.id = 'orbit-site-theme';
            style.textContent = {json.dumps(css)};
            (document.head || document.documentElement).appendChild(style);
        }})();
        """
        self.page().runJavaScript(js)


class OrbitBrowser(QMainWindow):
    identityChanged = Signal()

    def __init__(self, session, config):
        super().__init__()
        self.token = session.get("token")
        self.user = session["user"]
        self.is_guest = bool(session.get("guest")) or not self.token
        self.config = config
        self.current_theme = config.get("theme", "VOID")
        self.API_URL = API_URL
        self.THEMES = THEMES
        self.web_profile = QWebEngineProfile.defaultProfile()
        self.web_profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        cache_root = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "OrbitBrowser", "cache", "webengine")
        storage_root = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "OrbitBrowser", "data", "webengine")
        os.makedirs(cache_root, exist_ok=True)
        os.makedirs(storage_root, exist_ok=True)
        try:
            self.web_profile.setCachePath(cache_root)
            self.web_profile.setPersistentStoragePath(storage_root)
            self.web_profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
            self.web_profile.setHttpCacheMaximumSize(256 * 1024 * 1024)
        except Exception:
            pass
        self.setWindowTitle("Orbit Browser")
        icon_path = resource_path("assets", "orbit_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1500, 920)
        self.setMinimumSize(1100, 700)
        self.config["stats_sessions"] = int(self.config.get("stats_sessions", 0)) + 1
        save_config(self.config)
        save_local_profile(self.user)
        self.build_ui()
        self.update_identity_ui()
        self.apply_theme()
        self.show_home_screen()
        self.update_timer = QTimer(self)
        QTimer.singleShot(2500, self.check_updates)
        self.update_timer.setInterval(30 * 60 * 1000)
        self.update_timer.timeout.connect(self.check_updates)
        self.update_timer.start()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        self.sidebar = sidebar
        sidebar.setFixedWidth(208)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(14, 16, 14, 16)
        side.setSpacing(7)

        logo = QLabel("◉  ORBIT")
        logo.setObjectName("brandHero")
        side.addWidget(logo)

        nav = [
            ("⌂", "home", self.show_home_screen),
            ("▣", "tabs", self.show_web_area),
            ("◷", "history", self.open_history),
            ("☆", "bookmarks", self.open_bookmarks),
            ("↓", "downloads", self.open_downloads),
            ("✦", "gemini", self.open_gemini),
            ("❔", "support", self.open_support),
            ("✎", "notes", self.open_notes),
            ("⚙", "settings", self.open_settings),
        ]
        role = self.user.get("role", "user").lower()
        if self.is_guest:
            nav = [
                ("⌂", "home", self.show_home_screen),
                ("▣", "tabs", self.show_web_area),
                ("◷", "history", self.open_history),
                ("☆", "bookmarks", self.open_bookmarks),
                ("↓", "downloads", self.open_downloads),
                ("✦", "gemini", self.open_gemini),
                ("⚙", "settings", self.open_settings),
            ]
        elif role in {"helper", "admin"}:
            nav.insert(-1, ("◆", "admin", self.open_admin_panel))
        self.nav_buttons = {}
        for icon_text, key, fn in nav:
            button = QPushButton(f"{icon_text}   {tr(self.config.get('language', 'ru'), key)}")
            button.setObjectName("sidebarNav")
            button.clicked.connect(fn)
            side.addWidget(button)
            self.nav_buttons[key] = (button, icon_text)

        side.addStretch()

        root.addWidget(sidebar)

        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(7)

        chrome = QFrame()
        chrome.setObjectName("chromeBar")
        top = QHBoxLayout(chrome)
        top.setContentsMargins(9, 7, 9, 7)
        top.setSpacing(4)

        self.sidebar_toggle_button = QPushButton("☰")
        self.sidebar_toggle_button.setFixedSize(42, 42)
        self.sidebar_toggle_button.setToolTip("Скрыть/показать боковую панель")
        self.sidebar_toggle_button.clicked.connect(self.toggle_sidebar)
        top.addWidget(self.sidebar_toggle_button)

        # Restore the sidebar visibility saved by the user.
        if self.config.get("sidebar_hidden", False):
            self.sidebar.setMinimumWidth(0)
            self.sidebar.setMaximumWidth(0)
            self.sidebar.hide()
            self.sidebar_toggle_button.setToolTip("Показать боковую панель")

        for text, fn in [
            ("‹", self.go_back),
            ("›", self.go_forward),
            ("↻", self.reload_page),
            ("⌂", self.show_home_screen),
        ]:
            button = QPushButton(text)
            button.setFixedSize(42, 42)
            button.clicked.connect(fn)
            top.addWidget(button)

        self.address = QLineEdit()
        self.address.setPlaceholderText("Введите запрос или URL...")
        self.address.returnPressed.connect(self.navigate)
        top.addWidget(self.address, 1)

        profile = QPushButton(self.user.get("display_name") or self.user.get("username", "Аккаунт"))
        profile.setObjectName("topProfile")
        profile.setMinimumSize(150, 42)
        profile.setMaximumWidth(190)
        self.top_profile_button = profile
        profile.clicked.connect(self.open_profile_page)
        top.addWidget(profile)

        content.addWidget(chrome)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.tabBar().setExpanding(False)
        self.tabs.tabBar().setElideMode(Qt.TextElideMode.ElideRight)
        self.update_tab_widths()
        self.tabs.setElideMode(Qt.TextElideMode.ElideRight)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.tabBar().setExpanding(False)
        self.tabs.tabBar().setMinimumWidth(180)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.sync_address)
        self.tabs.currentChanged.connect(lambda _i: self.update_tab_widths())
        self.close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        self.close_shortcut.activated.connect(self.close_current_tab)
        self.admin_shortcut = QShortcut(QKeySequence("Ctrl+Shift+A"), self)
        self.admin_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.admin_shortcut.activated.connect(self.open_admin_panel)

        self.home = HomePage(self)
        home_index = self.tabs.addTab(self.home, "Главная")
        self.install_tab_close_button(home_index)
        self.home.weatherChanged.connect(self.sync_sidebar_weather)
        self.sync_sidebar_weather(self.home.weather_button.text())
        self.web_area = self.tabs
        content.addWidget(self.web_area, 1)

        self.web_profile.downloadRequested.connect(self.handle_download_request)

        root.addLayout(content, 1)
    def toggle_sidebar(self):
        if not hasattr(self, "sidebar") or not hasattr(self, "sidebar_toggle_button"):
            return

        # Hide the sidebar by collapsing its layout slot as well as the widget.
        # This makes the content area expand immediately and avoids the sidebar
        # keeping an invisible 208px gap in the layout.
        currently_visible = self.sidebar.isVisible() and self.sidebar.maximumWidth() > 0
        should_hide = currently_visible

        if should_hide:
            self.sidebar.setMaximumWidth(0)
            self.sidebar.setMinimumWidth(0)
            self.sidebar.hide()
            self.config["sidebar_hidden"] = True
            self.sidebar_toggle_button.setText("☰")
            self.sidebar_toggle_button.setToolTip("Показать боковую панель")
        else:
            self.sidebar.show()
            self.sidebar.setMinimumWidth(208)
            self.sidebar.setMaximumWidth(208)
            self.config["sidebar_hidden"] = False
            self.sidebar_toggle_button.setText("☰")
            self.sidebar_toggle_button.setToolTip("Скрыть боковую панель")

        self.sidebar.updateGeometry()
        save_config(self.config)

    def sync_sidebar_weather(self, text):
        if hasattr(self, "sidebar_weather"):
            self.sidebar_weather.setText(text.replace("  ", " ", 1))

    def open_weather_from_sidebar(self):
        self.show_home_screen()
        self.home.open_weather_dialog()
        self.sync_sidebar_weather(self.home.weather_button.text())

    def apply_language(self):
        language = self.config.get("language", "ru")
        if hasattr(self, "nav_buttons"):
            for key, (button, icon_text) in self.nav_buttons.items():
                button.setText(f"{icon_text}   {tr(language, key)}")
                button.setVisible(key not in set(self.config.get("hidden_nav", [])))
        if hasattr(self, "sidebar_weather"):
            self.sidebar_weather.setToolTip("Погода" if language == "ru" else "Weather")
        if hasattr(self, "home"):
            self.home.apply_language()
        self.setWindowTitle("Orbit Browser" if language == "en" else "Orbit Browser")
        save_config(self.config)

    def apply_theme(self):
        QApplication.instance().setStyleSheet(stylesheet(self.current_theme))
        if hasattr(self, "home") and self.config.get("site_theming", True):
            pass
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

    def show_home_screen(self):
        if hasattr(self, "tabs"):
            self.tabs.setCurrentWidget(self.home)
        self.address.clear()
        self.home.refresh_shortcuts()

    def show_web_area(self):
        if hasattr(self, "tabs") and self.tabs.currentWidget() is self.home:
            return
        self.web_area.setVisible(True)

    def new_browser_tab(self, url=None):
        self.show_web_area()
        browser = BrowserView(self.web_profile, self)
        browser.urlChanged.connect(lambda u, b=browser: self.browser_url_changed(b, u))
        browser.titleChanged.connect(lambda t, b=browser: self.browser_title_changed(b, t))
        browser.setUrl(QUrl(url or "about:blank"))
        i = self.tabs.addTab(browser, "Новая вкладка")
        self.install_tab_close_button(i)
        self.tabs.setCurrentIndex(i)
        return browser

    def current_browser(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, QWebEngineView) else None

    def install_tab_close_button(self, index):
        if index < 0 or index >= self.tabs.count():
            return
        button = QPushButton("×")
        button.setObjectName("tabCloseButton")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip("Закрыть вкладку / Close tab")
        button.setFixedSize(22, 22)
        button.clicked.connect(lambda _checked=False, b=button: self.close_tab_by_button(b))
        self.tabs.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, button)

    def close_tab_by_button(self, button):
        for i in range(self.tabs.count()):
            if self.tabs.tabBar().tabButton(i, QTabBar.ButtonPosition.RightSide) is button:
                self.close_tab(i)
                return

    def close_current_tab(self):
        if self.tabs.count() == 0:
            return
        self.close_tab(self.tabs.currentIndex())

    def close_tab(self, index):
        if index < 0 or index >= self.tabs.count():
            return
        if self.tabs.widget(index) is self.home:
            if self.tabs.count() > 1:
                self.tabs.setCurrentIndex(1)
            return
        w = self.tabs.widget(index)
        self.tabs.removeTab(index)
        if w is not None:
            w.deleteLater()
        if self.tabs.count() == 0:
            home_index = self.tabs.addTab(self.home, "Главная")
            self.install_tab_close_button(home_index)
            self.tabs.setCurrentIndex(home_index)

    def handle_download_request(self, item):
        try:
            default_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
            os.makedirs(default_dir, exist_ok=True)
            filename = item.downloadFileName() or item.suggestedFileName() or "OrbitDownload"
            path = os.path.join(default_dir, filename)
            base, ext = os.path.splitext(path)
            counter = 1
            while os.path.exists(path):
                path = f"{base} ({counter}){ext}"
                counter += 1
            item.setDownloadDirectory(default_dir)
            item.setDownloadFileName(os.path.basename(path))
            add_download(os.path.basename(path), item.url().toString(), path, "started", 0)
            def done():
                add_download(os.path.basename(path), item.url().toString(), path, "completed", 0)
            item.isFinishedChanged.connect(done)
            item.accept()
        except Exception:
            try:
                item.accept()
            except Exception:
                pass

    def browser_title_changed(self, browser, title):
        i = self.tabs.indexOf(browser)
        if i < 0:
            return
        title = title.strip() or "Новая вкладка"
        self.tabs.setTabText(i, title[:22] + ("…" if len(title) > 22 else ""))

    def browser_url_changed(self, browser, url):
        value = url.toString()
        if browser is self.current_browser():
            self.address.setText(value)
        if value and not value.startswith(("about:", "orbit://")):
            add_history(browser.title() or value, value)
            self.config["stats_pages"] = int(self.config.get("stats_pages", 0)) + 1
            save_config(self.config)

    def sync_address(self, index):
        browser = self.current_browser()
        self.address.setText(browser.url().toString() if browser else "")
        self.update_tab_widths()

    def update_tab_widths(self):
        if not hasattr(self, "tabs"):
            return
        count = max(1, self.tabs.count())
        available = max(240, self.tabs.tabBar().width() - 16)
        width = max(72, min(190, int(available / count) - 8))
        self.tabs.setStyleSheet(
            f"QTabBar::tab {{ min-width: {width}px; max-width: {width}px; padding: 7px 8px; }} "
            "QTabBar::close-button { width: 16px; height: 16px; }"
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.update_tab_widths)

    def navigate(self):
        text = self.address.text().strip()
        if not text:
            return
        self.navigate_text(text)

    def navigate_text(self, text):
        text = text.strip()
        if not text:
            return
        if text.startswith(("http://", "https://")):
            self.config["stats_pages"] = int(self.config.get("stats_pages", 0)) + 1
            save_config(self.config)
            self.open_url(text)
        elif "." in text and " " not in text:
            self.config["stats_pages"] = int(self.config.get("stats_pages", 0)) + 1
            save_config(self.config)
            self.open_url("https://" + text)
        else:
            self.open_orbit_search(text)

    SEARCH_PROVIDERS = {
        "google": "https://www.google.com/search?q=",
        "bing": "https://www.bing.com/search?q=",
        "duckduckgo": "https://duckduckgo.com/?q=",
        "orbit": "https://www.google.com/search?q=",
    }

    def search_url(self, query):
        base = self.SEARCH_PROVIDERS.get(self.config.get("search_engine", "google"), self.SEARCH_PROVIDERS["google"])
        return base + quote(query)

    def open_orbit_search(self, query=""):
        if query:
            self.open_url(self.search_url(query))
            return
        self.show_web_area()
        page = SearchPage(self, query)
        i = self.tabs.addTab(page, "Поиск")
        self.tabs.setCurrentIndex(i)
        self.address.setText("orbit://search")

    def open_url(self, url):
        if not url.startswith("orbit://") and not self.network_allowed():
            QMessageBox.warning(self, "Orbit Network", "Orbit настроен работать только при наличии VPN. Включите VPN или отключите эту защиту в Настройках.")
            return
        if url.startswith("orbit://history"):
            self.open_internal_page(HistoryPage(self), "История")
            return
        if url.startswith("orbit://bookmarks"):
            self.open_internal_page(BookmarksPage(self), "Закладки")
            return
        if url.startswith("orbit://downloads"):
            self.open_internal_page(DownloadsPage(self), "Загрузки")
            return
        if url.startswith("orbit://notes"):
            self.open_internal_page(NotesPage(self), "Notes")
            return
        if url.startswith("orbit://settings"):
            self.open_internal_page(SettingsPage(self), "Настройки")
            return
        if url.startswith("orbit://profile"):
            self.open_profile_page()
            return
        if url.startswith("orbit://gemini"):
            self.open_gemini()
            return
        if url.startswith("orbit://support"):
            self.open_support()
            return
        self.show_web_area()
        browser = self.current_browser()
        if not browser:
            browser = self.new_browser_tab(url)
        else:
            browser.setUrl(QUrl(url))

    def vpn_available(self):
        if not self.config.get("require_vpn", False):
            return True
        if sys.platform != "win32":
            return True
        try:
            text = subprocess.check_output(["ipconfig", "/all"], text=True, encoding="utf-8", errors="ignore")
            keywords = ("wireguard", "wintun", "openvpn", "nordvpn", "mullvad", "proton", "tailscale", "warp", "tap-windows", "cisco anyconnect")
            return any(k in text.lower() for k in keywords)
        except Exception:
            return True

    def network_allowed(self):
        return self.vpn_available()

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
        self.show_web_area()
        i = self.tabs.addTab(page, title)
        self.install_tab_close_button(i)
        self.tabs.setCurrentIndex(i)
        self.address.setText(f"orbit://{title.lower()}")

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

    def open_profile_page(self):
        if self.is_guest:
            # Для гостя верхняя кнопка является компактной точкой входа.
            # Открываем официальный Orbit-сайт в текущей вкладке, где доступны вход и регистрация.
            self.show_web_area()
            browser = self.current_browser()
            login_url = self.API_URL.rstrip("/") + "/"
            if not browser:
                browser = self.new_browser_tab(login_url)
            else:
                browser.setUrl(QUrl(login_url))
            self.address.setText(login_url)
            return
        self.open_internal_page(ProfilePage(self), "Профиль")

    def open_gemini(self):
        # Orbit AI is a simple, convenient Gemini web-chat entry point.
        # No Gemini API key is embedded in the desktop client.
        self.show_web_area()
        browser = self.current_browser()
        gemini_url = "https://gemini.google.com/app"
        if not browser:
            browser = self.new_browser_tab(gemini_url)
        else:
            browser.setUrl(QUrl(gemini_url))
        self.address.setText(gemini_url)

    def open_support(self):
        if self.is_guest:
            QMessageBox.information(self, "Orbit Помощь", "Чтобы создавать и отслеживать обращения, войдите в Orbit Account.")
            return
        self.open_internal_page(SupportPage(self), "Помощь")

    def open_admin_panel(self):
        if self.is_guest or self.user.get("role", "user").lower() not in {"helper", "admin"}:
            return
        self.open_internal_page(AdminPanelPage(self), "Админ-панель")

    def open_profile(self):
        self.open_profile_page()

    def open_menu(self):
        bar = self.menuBar()
        bar.clear()
        m = bar.addMenu("Orbit")
        entries = [
            ("Главная", self.show_home_screen),
            ("История", self.open_history),
            ("Закладки", self.open_bookmarks),
            ("Загрузки", self.open_downloads),
            ("Notes", self.open_notes),
            ("Orbit AI", self.open_gemini),
            ("Помощь", self.open_support),
            ("Профиль", self.open_profile_page),
            ("Диагностика", self.open_diagnostics),
            ("Настройки", self.open_settings),
        ]
        if self.user.get("role", "user").lower() in {"helper", "admin"} and not self.is_guest:
            entries.insert(-1, ("Админ-панель", self.open_admin_panel))
        for text, fn in entries:
            action = QAction(text, self)
            action.triggered.connect(fn)
            m.addAction(action)
        bar.setVisible(True)

    def open_diagnostics(self):
        self.open_internal_page(DiagnosticsPage(self), "Диагностика")

    def update_identity_ui(self):
        name = self.user.get("display_name") or self.user.get("username", "Аккаунт")
        if self.is_guest:
            name = "Войти"
        if hasattr(self, "account_button"):
            self.account_button.setText(name)
        if hasattr(self, "top_profile_button"):
            self.top_profile_button.setText(name)
            title = self.user.get("equipped_title") or self.user.get("title") or "Explorer"
            self.top_profile_button.setToolTip(f"{name} · {title}")
            try:
                avatar_path = self.config.get("avatar_path", "")
                if avatar_path and os.path.exists(avatar_path):
                    pix = QPixmap(avatar_path).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                    self.top_profile_button.setIcon(QIcon(pix))
                    self.top_profile_button.setIconSize(QSize(32, 32))
                else:
                    self.top_profile_button.setIcon(QIcon())
            except Exception:
                pass
        try:
            self.identityChanged.emit()
        except Exception:
            pass

    @staticmethod
    def _version_tuple(value):
        nums = []
        for part in str(value).split("."):
            digits = "".join(ch for ch in part if ch.isdigit())
            nums.append(int(digits or 0))
        return tuple((nums + [0, 0, 0])[:3])

    def check_updates(self):
        if not self.config.get("auto_update", True):
            return
        try:
            response = requests.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                headers={"Accept": "application/vnd.github+json"},
                timeout=8,
            )
            if response.status_code != 200:
                return
            release = response.json()
            tag = str(release.get("tag_name", "")).lstrip("v")
            if not tag or self._version_tuple(tag) <= self._version_tuple(APP_VERSION):
                return
            asset = next((a for a in release.get("assets", []) if a.get("name") == "OrbitBrowser-Setup.exe"), None)
            if not asset:
                return
            answer = QMessageBox.question(
                self,
                "Доступно обновление",
                f"Доступна новая версия Orbit Browser {tag}.\n\nТекущая: {APP_VERSION}\nНовая: {tag}\n\nУстановить обновление сейчас?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            self.download_and_launch_update(asset["browser_download_url"], tag)
        except Exception:
            return

    def download_and_launch_update(self, url, version):
        progress = QProgressDialog("Загрузка обновления…", "Отмена", 0, 100, self)
        progress.setWindowTitle("Orbit Browser — обновление")
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        temp_dir = tempfile.mkdtemp(prefix="orbit_update_")
        installer = os.path.join(temp_dir, "OrbitBrowser-Setup.exe")
        try:
            with requests.get(url, stream=True, timeout=30, headers={"Accept": "application/octet-stream"}) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                done = 0
                with open(installer, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 128):
                        if progress.wasCanceled():
                            progress.close()
                            return
                        if chunk:
                            f.write(chunk)
                            done += len(chunk)
                            if total:
                                progress.setValue(int(done * 100 / total))
                                progress.setLabelText(f"Скачивание {done // 1024 // 1024} / {total // 1024 // 1024} МБ…")
                            QApplication.processEvents()
            progress.setValue(100)
            progress.setLabelText(f"Запуск установщика Orbit Browser {version}…")
            QApplication.processEvents()
            subprocess.Popen([installer], close_fds=True)
            QTimer.singleShot(300, QApplication.instance().quit)
        except Exception as exc:
            progress.close()
            QMessageBox.warning(self, "Не удалось обновить Orbit", str(exc))


def main():
    configure_windows_identity()
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    config = load_config()
    proxy_url = str(config.get("proxy_url", "")).strip()
    if proxy_url:
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--proxy-server=" + proxy_url
    app = QApplication(sys.argv)
    icon_path = resource_path("assets", "orbit_icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyleSheet(stylesheet(config.get("theme", "VOID")))

    print(f"Запуск {APP_NAME} {APP_VERSION}")

    splash = QSplashScreen(QPixmap(760, 390))
    splash.setStyleSheet("background:#07050d; color:#f6f1ff;")
    splash.showMessage(
        "ORBIT\n\nWelcome to Orbit Browser",
        Qt.AlignmentFlag.AlignCenter,
        Qt.GlobalColor.white,
    )
    splash.show()
    app.processEvents()
    if not check_api():
        QMessageBox.warning(None, "Orbit API", f"Orbit API недоступен.\n\n{API_URL}")
    session = load_session()
    if not session:
        session = {
            "token": None,
            "guest": True,
            "user": {
                "id": None,
                "username": "Guest",
                "display_name": "Гость",
                "bio": "",
                "title": "Гость",
                "equipped_title": "Гость",
                "unlocked_titles": [],
                "xp": 0,
                "profile_theme": config.get("theme", "VOID"),
                "role": "guest",
            },
        }
    local_profile = load_local_profile()
    if local_profile:
        merged = dict(session["user"])
        merged.update({k: v for k, v in local_profile.items() if k in {"display_name", "bio", "title", "profile_theme", "unlocked_titles", "equipped_title"}})
        session["user"] = merged
    window = OrbitBrowser(session, config)
    window.hide()

    def launch_main():
        window.show()
        splash.finish(window)

    QTimer.singleShot(1100, launch_main)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
