import json
import os
import sys
import shutil
import tempfile
import subprocess
from urllib.parse import quote

import requests
from PySide6.QtCore import QUrl, QTimer, Qt, QStandardPaths, QSize
from PySide6.QtGui import QAction, QPixmap, QIcon
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget, QSplashScreen, QProgressDialog, QFileDialog, QMenu, QStyle

from orbit_pages import HomePage, HistoryPage, BookmarksPage, NotesPage, DownloadsPage, SettingsPage, SearchPage, DiagnosticsPage, ProfilePage
from orbit_storage import load_config, save_config, load_local_profile, save_local_profile
from orbit_ui import THEMES, stylesheet, tr

APP_NAME = "Orbit Browser"
APP_VERSION = "1.11.0"
API_URL = "https://orbit-api-9uqa.onrender.com"
GITHUB_REPO = "larsendars-maker/OrbitBrowsers"


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
    def __init__(self, session, config):
        super().__init__()
        self.token = session["token"]
        self.user = session["user"]
        self.config = config
        self.current_theme = config.get("theme", "VOID")
        self.API_URL = API_URL
        self.THEMES = THEMES
        self.web_profile = QWebEngineProfile.defaultProfile()
        self.web_profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
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
        sidebar.setFixedWidth(184)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(12, 14, 12, 14)
        side.setSpacing(4)

        logo = QLabel("◉  ORBIT")
        logo.setObjectName("brandHero")
        side.addWidget(logo)

        nav = [
            ("⌂", "home", self.show_home_screen),
            ("▣", "tabs", self.show_web_area),
            ("◷", "history", self.open_history),
            ("☆", "bookmarks", self.open_bookmarks),
            ("↓", "downloads", self.open_downloads),
            ("✎", "notes", self.open_notes),
            ("⚙", "settings", self.open_settings),
        ]
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

        for text, fn in [
            ("‹", self.go_back),
            ("›", self.go_forward),
            ("↻", self.reload_page),
            ("⌂", self.show_home_screen),
        ]:
            button = QPushButton(text)
            button.setFixedSize(36, 36)
            button.clicked.connect(fn)
            top.addWidget(button)

        self.address = QLineEdit()
        self.address.setPlaceholderText("Введите запрос или URL...")
        self.address.returnPressed.connect(self.navigate)
        top.addWidget(self.address, 1)

        new_tab = QPushButton("+")
        new_tab.setFixedSize(36, 36)
        new_tab.clicked.connect(lambda: self.new_browser_tab())
        top.addWidget(new_tab)

        profile = QPushButton(self.user.get("display_name") or self.user.get("username", "Аккаунт"))
        self.top_profile_button = profile
        profile.clicked.connect(self.open_profile_page)
        top.addWidget(profile)

        content.addWidget(chrome)

        self.home = HomePage(self)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.sync_address)

        content.addWidget(self.home, 1)
        self.home.weatherChanged.connect(self.sync_sidebar_weather)
        self.sync_sidebar_weather(self.home.weather_button.text())
        self.web_area = self.tabs
        self.web_area.setVisible(False)
        content.addWidget(self.web_area, 1)

        root.addLayout(content, 1)
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
        self.web_area.setVisible(False)
        self.home.setVisible(True)
        self.address.clear()
        self.home.refresh_shortcuts()

    def show_web_area(self):
        self.home.setVisible(False)
        self.web_area.setVisible(True)

    def new_browser_tab(self, url=None):
        self.show_web_area()
        browser = BrowserView(self.web_profile, self)
        browser.urlChanged.connect(lambda u, b=browser: self.browser_url_changed(b, u))
        browser.titleChanged.connect(lambda t, b=browser: self.browser_title_changed(b, t))
        browser.setUrl(QUrl(url or "about:blank"))
        i = self.tabs.addTab(browser, "Новая вкладка")
        self.tabs.setCurrentIndex(i)
        return browser

    def current_browser(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, QWebEngineView) else None

    def close_tab(self, index):
        if self.tabs.count() <= 1:
            self.show_home_screen()
            return
        w = self.tabs.widget(index)
        self.tabs.removeTab(index)
        w.deleteLater()

    def browser_title_changed(self, browser, title):
        i = self.tabs.indexOf(browser)
        if i < 0:
            return
        title = title.strip() or "Новая вкладка"
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

    def open_orbit_search(self, query=""):
        engine = self.config.get("search_engine", "google")
        engines = {
            "orbit": "https://www.google.com/search?q=",
            "google": "https://www.google.com/search?q=",
            "bing": "https://www.bing.com/search?q=",
            "duckduckgo": "https://duckduckgo.com/?q=",
        }
        base = engines.get(engine, engines["google"])
        if query:
            self.open_url(base + quote(query))
            return
        self.show_web_area()
        page = SearchPage(self, query)
        i = self.tabs.addTab(page, "Поиск")
        self.tabs.setCurrentIndex(i)
        self.address.setText("orbit://search")

    def open_url(self, url):
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
        self.show_web_area()
        browser = self.current_browser()
        if not browser:
            browser = self.new_browser_tab(url)
        else:
            browser.setUrl(QUrl(url))

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
        self.open_internal_page(ProfilePage(self), "Профиль")

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
            ("Профиль", self.open_profile_page),
            ("Диагностика", self.open_diagnostics),
            ("Настройки", self.open_settings),
        ]
        for text, fn in entries:
            action = QAction(text, self)
            action.triggered.connect(fn)
            m.addAction(action)
        bar.setVisible(True)

    def open_diagnostics(self):
        self.open_internal_page(DiagnosticsPage(self), "Диагностика")

    def update_identity_ui(self):
        name = self.user.get("display_name") or self.user.get("username", "Аккаунт")
        if hasattr(self, "account_button"):
            self.account_button.setText(name)
        if hasattr(self, "top_profile_button"):
            self.top_profile_button.setText(name)
            try:
                avatar_path = self.config.get("avatar_path", "")
                if avatar_path and os.path.exists(avatar_path):
                    pix = QPixmap(avatar_path).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                    self.top_profile_button.setIcon(QIcon(pix))
                    self.top_profile_button.setIconSize(QSize(24, 24))
                else:
                    self.top_profile_button.setIcon(QIcon())
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
            progress.setLabelText("Запуск установщика…")
            QApplication.processEvents()
            subprocess.Popen([installer], close_fds=True)
            QTimer.singleShot(300, QApplication.instance().quit)
        except Exception as exc:
            progress.close()
            QMessageBox.warning(self, "Не удалось обновить Orbit", str(exc))


def main():
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    config = load_config()
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
        QMessageBox.warning(None, "Orbit Browser", "Сохранённая сессия не найдена.\n\nСначала войдите в Orbit.")
        sys.exit(0)
    local_profile = load_local_profile()
    if local_profile:
        merged = dict(session["user"])
        merged.update({k: v for k, v in local_profile.items() if k in {"display_name", "bio", "title", "profile_theme"}})
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
