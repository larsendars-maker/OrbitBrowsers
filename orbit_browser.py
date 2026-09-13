import json
import os
import sys
from urllib.parse import quote

import requests

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
QApplication,
QComboBox,
QLineEdit,
QMainWindow,
QMessageBox,
QPushButton,
QTabWidget,
QVBoxLayout,
QHBoxLayout,
QWidget,
QLabel,
QFrame,
)

from orbit_pages import (
HomePage,
HistoryPage,
BookmarksPage,
NotesPage,
DownloadsPage,
SettingsPage,
)

from orbit_storage import (
load_config,
save_config,
)

from orbit_ui import (
THEMES,
stylesheet,
)

APP_NAME = "Orbit Browser"
APP_VERSION = "0.5.0"

API_URL = "https://orbit-api-9uqa.onrender.com"

SESSION_FILE = os.path.join(
os.environ.get(
"LOCALAPPDATA",
os.path.expanduser("~"),
),
"OrbitBrowser",
"data",
"session.json",
)

def check_api():
try:
response = requests.get(
f"{API_URL}/health",
timeout=10,
)

```
    return response.status_code == 200

except Exception:
    return False
```

def load_session():
if not os.path.exists(SESSION_FILE):
return None

```
try:
    with open(
        SESSION_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        saved = json.load(file)

    token = saved.get("token")

    if not token:
        return None

    response = requests.get(
        f"{API_URL}/api/auth/session",
        headers={
            "Authorization": f"Bearer {token}",
        },
        timeout=15,
    )

    if response.status_code != 200:
        return None

    data = response.json()

    if not data.get("ok"):
        return None

    user = data.get("user")

    if not user:
        return None

    session = {
        "token": token,
        "user": user,
    }

    os.makedirs(
        os.path.dirname(SESSION_FILE),
        exist_ok=True,
    )

    with open(
        SESSION_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            session,
            file,
            ensure_ascii=False,
            indent=4,
        )

    return session

except Exception:
    return None
```

class BrowserView(QWebEngineView):

```
def __init__(
    self,
    profile,
    parent=None,
):
    super().__init__(parent)

    page = profile.createStandardPage()

    self.setPage(page)

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
```

class OrbitBrowser(QMainWindow):

```
def __init__(
    self,
    session,
    config,
):
    super().__init__()

    self.token = session["token"]
    self.user = session["user"]

    self.config = config

    self.current_theme = config.get(
        "theme",
        "VOID",
    )

    self.web_profile = (
        QWebEngineProfile.defaultProfile()
    )

    self.web_profile.setPersistentCookiesPolicy(
        QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
    )

    self.setWindowTitle(
        "Orbit Browser"
    )

    self.resize(
        1450,
        900,
    )

    self.build_ui()
    self.apply_theme()
    self.open_home()

# ========================================================
# UI
# ========================================================

def build_ui(self):

    central = QWidget()

    self.setCentralWidget(
        central
    )

    root = QVBoxLayout(
        central
    )

    root.setContentsMargins(
        8,
        8,
        8,
        8,
    )

    root.setSpacing(
        7
    )

    toolbar_frame = QFrame()

    toolbar_frame.setObjectName(
        "toolbar"
    )

    toolbar = QHBoxLayout(
        toolbar_frame
    )

    toolbar.setContentsMargins(
        8,
        8,
        8,
        8,
    )

    back = QPushButton(
        "←"
    )

    forward = QPushButton(
        "→"
    )

    reload_button = QPushButton(
        "⟳"
    )

    home = QPushButton(
        "⌂"
    )

    for button in [
        back,
        forward,
        reload_button,
        home,
    ]:
        button.setFixedWidth(
            40
        )

    back.clicked.connect(
        self.go_back
    )

    forward.clicked.connect(
        self.go_forward
    )

    reload_button.clicked.connect(
        self.reload_page
    )

    home.clicked.connect(
        self.open_home
    )

    self.address = QLineEdit()

    self.address.setPlaceholderText(
        "Поиск или адрес..."
    )

    self.address.returnPressed.connect(
        self.navigate
    )

    new_tab = QPushButton(
        "+"
    )

    new_tab.setFixedWidth(
        40
    )

    new_tab.clicked.connect(
        self.new_browser_tab
    )

    profile_button = QPushButton(
        self.user.get(
            "display_name",
            self.user.get(
                "username",
                "Profile",
            ),
        )
    )

    profile_button.clicked.connect(
        self.open_profile
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

    menu = QPushButton(
        "⋮"
    )

    menu.setFixedWidth(
        40
    )

    menu.clicked.connect(
        self.open_menu
    )

    toolbar.addWidget(
        back
    )

    toolbar.addWidget(
        forward
    )

    toolbar.addWidget(
        reload_button
    )

    toolbar.addWidget(
        home
    )

    toolbar.addWidget(
        self.address,
        1
    )

    toolbar.addWidget(
        new_tab
    )

    toolbar.addWidget(
        profile_button
    )

    toolbar.addWidget(
        self.theme_combo
    )

    toolbar.addWidget(
        menu
    )

    root.addWidget(
        toolbar_frame
    )

    self.tabs = QTabWidget()

    self.tabs.setTabsClosable(
        True
    )

    self.tabs.tabCloseRequested.connect(
        self.close_tab
    )

    self.tabs.currentChanged.connect(
        self.sync_address
    )

    root.addWidget(
        self.tabs,
        1
    )

# ========================================================
# THEME
# ========================================================

def apply_theme(self):

    QApplication.instance().setStyleSheet(
        stylesheet(
            self.current_theme
        )
    )

def change_theme(
    self,
    theme,
):

    if theme not in THEMES:
        return

    self.current_theme = theme

    self.config["theme"] = theme

    save_config(
        self.config
    )

    self.apply_theme()

# ========================================================
# TABS
# ========================================================

def new_browser_tab(
    self,
    url=None,
):

    browser = BrowserView(
        self.web_profile
    )

    browser.urlChanged.connect(
        lambda value, b=browser:
        self.browser_url_changed(
            b,
            value,
        )
    )

    browser.titleChanged.connect(
        lambda title, b=browser:
        self.browser_title_changed(
            b,
            title,
        )
    )

    if url:
        browser.setUrl(
            QUrl(url)
        )
    else:
        browser.setUrl(
            QUrl("about:blank")
        )

    index = self.tabs.addTab(
        browser,
        "Новая вкладка",
    )

    self.tabs.setCurrentIndex(
        index
    )

    return browser

def current_browser(self):

    widget = self.tabs.currentWidget()

    if isinstance(
        widget,
        QWebEngineView,
    ):
        return widget

    return None

def close_tab(
    self,
    index,
):

    if self.tabs.count() <= 1:

        self.open_home()

        return

    widget = self.tabs.widget(
        index
    )

    self.tabs.removeTab(
        index
    )

    widget.deleteLater()

def browser_title_changed(
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

    if len(title) > 25:
        title = (
            title[:25]
            + "..."
        )

    self.tabs.setTabText(
        index,
        title,
    )

def browser_url_changed(
    self,
    browser,
    url,
):

    if browser is self.current_browser():

        self.address.setText(
            url.toString()
        )

def sync_address(
    self,
    index,
):

    browser = self.current_browser()

    if browser:

        self.address.setText(
            browser.url().toString()
        )

    else:

        self.address.clear()

# ========================================================
# NAVIGATION
# ========================================================

def navigate(self):

    text = (
        self.address.text().strip()
    )

    if not text:
        return

    self.navigate_text(
        text
    )

def navigate_text(
    self,
    text,
):

    text = text.strip()

    if not text:
        return

    if text.startswith(
        (
            "http://",
            "https://",
        )
    ):

        url = text

    elif "." in text and " " not in text:

        url = (
            "https://"
            + text
        )

    else:

        search_engine = self.config.get(
            "search_engine",
            "https://www.google.com/search?q=",
        )

        url = (
            search_engine
            + quote(text)
        )

    browser = self.current_browser()

    if not browser:

        browser = self.new_browser_tab()

    browser.setUrl(
        QUrl(url)
    )

def open_url(
    self,
    url,
):

    browser = self.current_browser()

    if not browser:

        browser = self.new_browser_tab()

    browser.setUrl(
        QUrl(url)
    )

def open_home(self):

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

# ========================================================
# CONTROLS
# ========================================================

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

# ========================================================
# INTERNAL PAGES
# ========================================================

def open_internal_page(
    self,
    page,
    title,
):

    index = self.tabs.addTab(
        page,
        title,
    )

    self.tabs.setCurrentIndex(
        index
    )

def open_history(self):

    self.open_internal_page(
        HistoryPage(self),
        "История",
    )

def open_bookmarks(self):

    self.open_internal_page(
        BookmarksPage(self),
        "Закладки",
    )

def open_notes(self):

    self.open_internal_page(
        NotesPage(self),
        "Notes",
    )

def open_downloads(self):

    self.open_internal_page(
        DownloadsPage(self),
        "Загрузки",
    )

def open_settings(self):

    self.open_internal_page(
        SettingsPage(self),
        "Настройки",
    )

# ========================================================
# PROFILE
# ========================================================

def open_profile(self):

    name = self.user.get(
        "display_name",
        self.user.get(
            "username",
            "User",
        ),
    )

    xp = int(
        self.user.get(
            "xp",
            0,
        )
    )

    level = (
        xp // 500
    ) + 1

    role = self.user.get(
        "role",
        "user",
    )

    role_text = (
        "Founder • Creator of Orbit"
        if role == "founder"
        else self.user.get(
            "title",
            "Explorer",
        )
    )

    QMessageBox.information(
        self,
        "Orbit Profile",
        (
            f"{name}\n\n"
            f"{role_text}\n"
            f"Level {level}\n"
            f"{xp} XP"
        ),
    )

# ========================================================
# MENU
# ========================================================

def open_menu(self):

    menu = self.menuBar()

    menu.clear()

    orbit_menu = menu.addMenu(
        "Orbit"
    )

    history = QAction(
        "История",
        self,
    )

    bookmarks = QAction(
        "Закладки",
        self,
    )

    downloads = QAction(
        "Загрузки",
        self,
    )

    notes = QAction(
        "Notes",
        self,
    )

    settings = QAction(
        "Настройки",
        self,
    )

    orbit_menu.addAction(
        history
    )

    orbit_menu.addAction(
        bookmarks
    )

    orbit_menu.addAction(
        downloads
    )

    orbit_menu.addAction(
        notes
    )

    orbit_menu.addSeparator()

    orbit_menu.addAction(
        settings
    )

    history.triggered.connect(
        self.open_history
    )

    bookmarks.triggered.connect(
        self.open_bookmarks
    )

    downloads.triggered.connect(
        self.open_downloads
    )

    notes.triggered.connect(
        self.open_notes
    )

    settings.triggered.connect(
        self.open_settings
    )

    menu.setVisible(
        True
    )
```

# ============================================================

# MAIN

# ============================================================

def main():

```
ensure_dir = os.path.dirname(
    SESSION_FILE
)

os.makedirs(
    ensure_dir,
    exist_ok=True,
)

config = load_config()

app = QApplication(
    sys.argv
)

app.setApplicationName(
    APP_NAME
)

app.setApplicationVersion(
    APP_VERSION
)

app.setStyleSheet(
    stylesheet(
        config.get(
            "theme",
            "VOID",
        )
    )
)

print(
    "Welcome to Orbit Browser"
)

if not check_api():

    QMessageBox.warning(
        None,
        "Orbit API",
        (
            "Orbit API недоступен.\n\n"
            f"{API_URL}"
        ),
    )

session = load_session()

if not session:

    QMessageBox.warning(
        None,
        "Orbit Browser",
        (
            "Сохранённая сессия не найдена.\n\n"
            "Сначала войдите в Orbit через "
            "рабочую версию клиента."
        ),
    )

    sys.exit(0)

window = OrbitBrowser(
    session,
    config,
)

window.show()

sys.exit(
    app.exec()
)
```

if **name** == "**main**":
main()
