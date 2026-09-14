import json
import os
import sys
import shutil
import tempfile
import subprocess
from urllib.parse import quote

import requests
from PySide6.QtCore import QUrl, QTimer, Qt, QStandardPaths, QSize, Signal, QThread, QObject, QEasingCurve, QPropertyAnimation
from PySide6.QtGui import QAction, QPixmap, QIcon, QKeySequence, QShortcut
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QTabWidget, QVBoxLayout, QWidget, QSplashScreen, QProgressDialog, QFileDialog, QMenu, QStyle, QTabBar, QDialog, QComboBox

from orbit_pages import HomePage, HistoryPage, BookmarksPage, NotesPage, DownloadsPage, SettingsPage, SearchPage, DiagnosticsPage, ProfilePage, LoginPage, GeminiPage, SupportPage, AdminPanelPage
from orbit_storage import load_config, save_config, load_local_profile, save_local_profile, add_history, add_download, build_sync_bundle, apply_sync_bundle, sync_state_signature
from orbit_ui import THEMES, stylesheet, tr
from orbit_secure import protect as secure_protect, unprotect as secure_unprotect

APP_NAME = "Orbit Browser"
APP_VERSION = "1.6"
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
        raw_token = saved.get("token", "")
        try:
            token = secure_unprotect(raw_token) if raw_token.startswith("dpapi:") else raw_token
        except Exception:
            token = None
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
        self.loadFinished.connect(self._load_finished)

    def createWindow(self, _window_type):
        """Открывать target=_blank/window.open внутри новой вкладки Orbit, а не во внешнем окне."""
        try:
            return self.browser_window.new_browser_tab()
        except Exception:
            return None

    def _load_finished(self, ok):
        if not ok:
            try:
                self.browser_window.show_offline_page(self)
                return
            except Exception:
                pass
        self.apply_site_theme()

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


class SessionWorker(QObject):
    finished = Signal(object)

    def __init__(self, token):
        super().__init__()
        self.token = token

    def run(self):
        result = None
        if self.token:
            try:
                r = requests.get(f"{API_URL}/api/auth/session", headers={"Authorization": f"Bearer {self.token}"}, timeout=8)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("ok") and data.get("user"):
                        result = {"token": self.token, "user": data["user"]}
            except Exception:
                pass
        self.finished.emit(result)


class WelcomeOverlay(QFrame):
    done = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("welcomeOverlay")
        self.setStyleSheet("QFrame#welcomeOverlay{background:#07050d;border:none;} QLabel{color:white;}")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title = QLabel("WELCOM")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet("font-size:64px;font-weight:900;letter-spacing:12px;color:#f7f0ff;")
        self.subtitle = QLabel("ORBIT BROWSER")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setStyleSheet("font-size:11px;font-weight:700;letter-spacing:6px;color:#9f7cff;margin-top:8px;")
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        self.opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity)
        self.opacity.setOpacity(0.0)
        self.anim = QPropertyAnimation(self.opacity, b"opacity", self)
        self.anim.setDuration(850)
        self.anim.setStartValue(0.0)
        self.anim.setKeyValueAt(0.35, 1.0)
        self.anim.setKeyValueAt(0.78, 1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.anim.finished.connect(self._finish)

    def start(self):
        self.show()
        self.raise_()
        self.anim.start()

    def _finish(self):
        self.hide()
        self.done.emit()


class FirstRunGuide(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        self.setWindowTitle("Orbit Browser — первый запуск")
        self.setModal(True)
        self.resize(620, 520)
        self.setStyleSheet(stylesheet(browser.current_theme))
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 26, 28, 22)
        root.setSpacing(14)
        title = QLabel(tr(browser.config.get("language", "ru"), "guide_title"))
        title.setObjectName("pageTitle")
        root.addWidget(title)
        sub = QLabel(tr(browser.config.get("language", "ru"), "guide_sub"))
        sub.setObjectName("muted")
        root.addWidget(sub)

        def card(head, body):
            box = QFrame(); box.setObjectName("settingCard")
            lay = QVBoxLayout(box); lay.setContentsMargins(16, 12, 16, 12)
            h = QLabel(head); h.setObjectName("settingTitle")
            b = QLabel(body); b.setObjectName("settingDescription"); b.setWordWrap(True)
            lay.addWidget(h); lay.addWidget(b)
            root.addWidget(box)
        card("⚡ Производительность", "Максимальная скорость использует больше RAM/CPU, держит больше renderer-процессов и быстрее переключает вкладки. Сбалансированный режим экономит ресурсы.")
        card("🎨 Темы", "Выберите тему в Настройках. Изменение применяется сразу и сохраняется автоматически после закрытия окна.")
        card("🎮 Мини-игры", "Через кнопку «Мини-игры» можно открыть Snake и Block Blast прямо внутри Orbit. Игры работают и без интернета.")

        engine_row = QFrame(); engine_row.setObjectName("settingCard")
        er = QHBoxLayout(engine_row); er.setContentsMargins(16,12,16,12)
        et = QLabel("Поисковая система по умолчанию"); et.setObjectName("settingTitle")
        self.engine = QComboBox();
        for label, data in [("Google","google"),("Bing","bing"),("DuckDuckGo","duckduckgo"),("Яндекс","yandex")]: self.engine.addItem(label,data)
        idx = self.engine.findData(browser.config.get("search_engine","google")); self.engine.setCurrentIndex(idx if idx >= 0 else 0)
        er.addWidget(et,1); er.addWidget(self.engine)
        root.addWidget(engine_row)

        buttons = QHBoxLayout(); buttons.addStretch()
        ok = QPushButton("Понятно"); ok.setProperty("accent", True); ok.clicked.connect(self.accept)
        buttons.addWidget(ok); root.addLayout(buttons)

    def accept(self):
        self.browser.config["search_engine"] = self.engine.currentData() or "google"
        self.browser.config["first_run_guide_seen"] = True
        save_config(self.browser.config)
        if hasattr(self.browser, "home"):
            name = {"google":"Google","bing":"Bing","duckduckgo":"DuckDuckGo","yandex":"Яндекс"}.get(self.browser.config["search_engine"], "Google")
            self.browser.home.engine_hint.setText(name)
        super().accept()


class OrbitBrowser(QMainWindow):
    identityChanged = Signal()

    def __init__(self, session, config):
        super().__init__()
        self.token = session.get("token") if session else None
        self.user = session.get("user") if session else None
        # Анонимный режим не создаёт виртуального/гостевого пользователя.
        self.is_guest = not bool(self.token and self.user)
        self.config = config
        self._sync_last_signature = ""
        self._sync_running = False
        self._sync_timer = QTimer(self)
        self._sync_timer.setInterval(60000)
        self._sync_timer.timeout.connect(self.sync_now)
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
        if isinstance(self.user, dict):
            save_local_profile(self.user)
        self.build_ui()
        self.update_identity_ui()
        self.update_mode_button()
        self.apply_theme()
        self.show_home_screen()
        self.update_timer = QTimer(self)
        QTimer.singleShot(5000, self.check_updates)
        self.update_timer.setInterval(30 * 60 * 1000)
        self.update_timer.timeout.connect(self.check_updates)
        self.update_timer.start()
        self._sync_timer.start()
        QTimer.singleShot(6000, self.sync_now)

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
            ("◷", "history", self.open_history),
            ("☆", "bookmarks", self.open_bookmarks),
            ("↓", "downloads", self.open_downloads),
            ("✦", "gemini", self.open_gemini),
            ("❔", "support", self.open_support),
            ("✎", "notes", self.open_notes),
            ("🎮", "mini_games", self.open_mini_games),
            ("⚙", "settings", self.open_settings),
        ]
        role = (self.user or {}).get("role", "user").lower()
        if self.is_guest:
            nav = [
                ("⌂", "home", self.show_home_screen),
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

        profile = QPushButton((self.user or {}).get("display_name") or (self.user or {}).get("username", "Войти"))
        profile.setObjectName("topProfile")
        profile.setMinimumSize(150, 42)
        profile.setMaximumWidth(190)
        self.top_profile_button = profile
        profile.clicked.connect(self.open_profile_page)
        top.addWidget(profile)

        self.mode_button = QPushButton("⚡")
        self.mode_button.setFixedSize(42, 42)
        self.mode_button.setToolTip("Режим производительности")
        self.mode_button.clicked.connect(self.toggle_performance_mode)
        top.addWidget(self.mode_button)

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
    def performance_mode(self):
        return self.config.get("performance_mode", "performance")

    def toggle_performance_mode(self):
        current = self.performance_mode()
        new_mode = "balanced" if current == "performance" else "performance"
        self.config["performance_mode"] = new_mode
        save_config(self.config)
        self.apply_chromium_performance()
        self.update_mode_button()

    def update_mode_button(self):
        if not hasattr(self, "mode_button"):
            return
        if self.performance_mode() == "performance":
            self.mode_button.setText("⚡")
            self.mode_button.setToolTip("Режим: Производительность")
        else:
            self.mode_button.setText("◌")
            self.mode_button.setToolTip("Режим: Сбалансированный")

    def apply_chromium_performance(self):
        # Перезапуск процесса Chromium не нужен: применяем лёгкие настройки сразу,
        # а основные флаги задаются до создания QApplication.
        limit = 4 if self.performance_mode() == "performance" else 2
        try:
            os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = f"--disable-background-networking --disable-component-update --disable-domain-reliability --disable-features=Translate,MediaRouter,OptimizationHints --renderer-process-limit={limit}"
            if self.config.get("proxy_url"):
                os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] += " --proxy-server=" + str(self.config["proxy_url"])
        except Exception:
            pass

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

    def rebuild_navigation(self):
        # Rebuild the sidebar after login/session restore so role visibility updates immediately.
        current=self.tabs.currentWidget() if hasattr(self, "tabs") else None
        if hasattr(self, "sidebar") and self.sidebar.parentWidget():
            old=self.sidebar
            layout=old.parentWidget().layout()
            if layout:
                layout.removeWidget(old)
                old.deleteLater()
        # Lightweight refresh: rebuild the whole central UI while preserving the current tab widgets.
        if hasattr(self, "home"):
            self.update_identity_ui()

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

    def open_mini_games(self):
        """Открыть мини-игры в обычной вкладке Orbit, без отдельного окна."""
        from pathlib import Path
        candidates = [
            Path(__file__).with_name("web") / "games.html",
            Path(__file__).with_name("assets") / "offline.html",
        ]
        for path in candidates:
            if path.exists():
                browser = self.new_browser_tab(QUrl.fromLocalFile(str(path.resolve())))
                self.tabs.setTabText(self.tabs.currentIndex(), "Мини-игры")
                return browser
        QMessageBox.warning(self, "Orbit", "Файл мини-игр не найден.")
        return None

    def open_profile_page(self):
        if not self.token:
            self.open_internal_page(LoginPage(self), "Войти", "login")
            return
        self.open_internal_page(ProfilePage(self), "Профиль", "profile")

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
        self.open_internal_page(SupportPage(self), "Помощь", "support")

    def open_admin_panel(self):
        if self.is_guest or (self.user or {}).get("role", "user").lower() not in {"helper", "admin"}:
            return
        self.open_internal_page(AdminPanelPage(self), "Админ-панель", "admin")

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
            ("Мини-игры", self.open_mini_games),
        ]
        if (self.user or {}).get("role", "user").lower() in {"helper", "admin"} and not self.is_guest:
            entries.insert(-1, ("Админ-панель", self.open_admin_panel))
        for text, fn in entries:
            action = QAction(text, self)
            action.triggered.connect(fn)
            m.addAction(action)
        bar.setVisible(True)

    def open_diagnostics(self):
        self.open_internal_page(DiagnosticsPage(self), "Диагностика", "diagnostics")

    def update_identity_ui(self):
        user = self.user or {}
        name = user.get("display_name") or user.get("username", "Аккаунт")
        if self.is_guest:
            name = "Войти"
        if hasattr(self, "account_button"):
            self.account_button.setText(name)
        if hasattr(self, "top_profile_button"):
            self.top_profile_button.setText(name)
            title = user.get("equipped_title") or user.get("title") or "Explorer"
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

    def sync_now(self):
        if not self.token or self._sync_running: return
        bundle=build_sync_bundle(self.config,self.user)
        signature=sync_state_signature(bundle)
        self._sync_running=True
        outbound_bundle=bundle if signature != self._sync_last_signature else {}
        thread=QThread(self); worker=SyncRequestWorker(self.API_URL,self.token,outbound_bundle,signature if outbound_bundle else "")
        worker.moveToThread(thread); thread.started.connect(worker.run)
        def done(ok,remote):
            self._sync_running=False
            if ok and isinstance(remote,dict):
                apply_sync_bundle(remote,self.config)
                if remote.get("user"):
                    self.user=dict(self.user or {}); self.user.update(remote["user"]); save_local_profile(self.user)
                self._sync_last_signature=sync_state_signature(build_sync_bundle(self.config,self.user))
                self.update_identity_ui()
                self.rebuild_navigation()
            thread.quit()
        worker.finished.connect(done); thread.finished.connect(worker.deleteLater); thread.finished.connect(thread.deleteLater); thread.start()

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


class SyncRequestWorker(QObject):
    finished=Signal(bool,object)
    def __init__(self,api_url,token,bundle,signature):
        super().__init__(); self.api_url=api_url; self.token=token; self.bundle=bundle; self.signature=signature
    def run(self):
        try:
            headers={"Authorization":f"Bearer {self.token}"}
            if self.signature and self.bundle:
                r=requests.post(f"{self.api_url}/api/sync/state",json={"state":self.bundle,"signature":self.signature},headers=headers,timeout=8)
                if r.status_code==200:
                    self.finished.emit(True,r.json().get("state")); return
            r=requests.get(f"{self.api_url}/api/sync/state",headers=headers,timeout=8)
            if r.status_code==200:
                self.finished.emit(True,r.json().get("state")); return
            self.finished.emit(False,None)
        except Exception:
            self.finished.emit(False,None)


def main():
    configure_windows_identity()
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    config=load_config()
    flags=os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
    mode=str(config.get("performance_mode", "performance"))
    renderer_limit="4" if mode == "performance" else "2"
    optimizations=f" --disable-background-networking --disable-component-update --disable-domain-reliability --disable-features=Translate,MediaRouter,OptimizationHints --renderer-process-limit={renderer_limit}"
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"]=(flags+optimizations).strip()
    proxy_url=str(config.get("proxy_url", "")).strip()
    if proxy_url:
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] += " --proxy-server="+proxy_url
    app=QApplication(sys.argv)
    icon_path=resource_path("assets","orbit_icon.ico")
    if os.path.exists(icon_path): app.setWindowIcon(QIcon(icon_path))
    app.setApplicationName(APP_NAME); app.setApplicationVersion(APP_VERSION)
    app.setStyleSheet(stylesheet(config.get("theme","VOID")))
    local_profile=load_local_profile(); saved_token=None
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE,"r",encoding="utf-8") as f:
                saved_value=json.load(f).get("token")
                try:
                    saved_token=secure_unprotect(saved_value) if saved_value and saved_value.startswith("dpapi:") else saved_value
                except Exception:
                    saved_token=None
    except Exception: pass
    session={"token":saved_token if local_profile and saved_token else None, "user":local_profile if local_profile and saved_token else None}
    window=OrbitBrowser(session,config); window.show()
    welcome=WelcomeOverlay(window)
    welcome.setGeometry(window.rect())
    welcome.raise_()
    welcome.start()
    def after_welcome():
        if not window.config.get("first_run_guide_seen", False):
            QTimer.singleShot(180, lambda: FirstRunGuide(window, window).exec())
    welcome.done.connect(after_welcome)
    if saved_token:
        thread=QThread(app); worker=SessionWorker(saved_token); worker.moveToThread(thread); thread.started.connect(worker.run)
        def on_session(result):
            if result:
                window.token=result["token"]; window.user=result["user"]; window.is_guest=False; save_local_profile(window.user); window.update_identity_ui(); window.sync_now()
            thread.quit(); worker.deleteLater()
        worker.finished.connect(on_session); thread.finished.connect(thread.deleteLater); thread.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
