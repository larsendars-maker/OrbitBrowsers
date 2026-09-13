from html import escape
from urllib.parse import quote_plus

import requests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QVBoxLayout, QWidget,
)

from orbit_storage import add_bookmark, load_bookmarks, load_notes, save_notes
from orbit_ui import fade_in


class SearchPage(QWidget):
    def __init__(self, browser, query=""):
        super().__init__()
        self.browser = browser
        self.setObjectName("searchPage")
        self.build(query)

    def build(self, query):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(54, 48, 54, 40)
        layout.setSpacing(18)

        brand = QLabel("ORBIT")
        brand.setObjectName("searchBrand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(brand)

        tagline = QLabel("Search the web, the Orbit way.")
        tagline.setObjectName("muted")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tagline)

        shell = QFrame()
        shell.setObjectName("searchShell")
        row = QHBoxLayout(shell)
        row.setContentsMargins(10, 2, 10, 2)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Search the web or enter an address")
        self.input.setText(query)
        go = QPushButton("Search")
        go.setProperty("accent", True)
        row.addWidget(self.input, 1)
        row.addWidget(go)
        layout.addWidget(shell)
        self.input.returnPressed.connect(self.run_search)
        go.clicked.connect(self.run_search)

        self.results = QListWidget()
        layout.addWidget(self.results, 1)
        self.results.itemDoubleClicked.connect(self.open_item)

        if query:
            self.run_search()
        else:
            self.show_default()
        fade_in(self)

    def show_default(self):
        self.results.clear()
        items = [
            ("History", "Open your browsing history", "orbit://history"),
            ("Bookmarks", "Your saved pages", "orbit://bookmarks"),
            ("Notes", "Your Orbit notes", "orbit://notes"),
            ("Settings", "Customize Orbit", "orbit://settings"),
        ]
        for title, desc, url in items:
            item = QListWidgetItem(f"{title}\n{desc}")
            item.setData(Qt.ItemDataRole.UserRole, url)
            self.results.addItem(item)

    def run_search(self):
        text = self.input.text().strip()
        if not text:
            self.show_default()
            return
        if text.startswith(("http://", "https://")):
            self.browser.open_url(text)
            return
        if "." in text and " " not in text:
            self.browser.open_url("https://" + text)
            return
        self.results.clear()
        self.results.addItem(QListWidgetItem("Searching Orbit…"))
        try:
            r = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": text},
                headers={"User-Agent": "OrbitBrowser/1.0"},
                timeout=15,
            )
            r.raise_for_status()
            html = r.text
            # Lightweight extraction so Orbit owns the search page UI.
            import re
            matches = re.findall(
                r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
                html,
                flags=re.S | re.I,
            )
            self.results.clear()
            if not matches:
                self.results.addItem(QListWidgetItem("No results found."))
                return
            for url, title_html in matches[:20]:
                title = re.sub(r"<.*?>", "", title_html)
                item = QListWidgetItem(f"{title}\n{url}")
                item.setData(Qt.ItemDataRole.UserRole, url)
                self.results.addItem(item)
        except Exception as exc:
            self.results.clear()
            self.results.addItem(QListWidgetItem(f"Orbit Search error: {exc}"))

    def open_item(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            self.browser.open_url(url)


class HomePage(SearchPage):
    pass


class HistoryPage(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 30)
        title = QLabel("History")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        sub = QLabel("Pages you've visited in Orbit")
        sub.setObjectName("muted")
        layout.addWidget(sub)
        self.list = QListWidget()
        layout.addWidget(self.list, 1)
        self.refresh()
        self.list.itemDoubleClicked.connect(self.open_item)
        fade_in(self)

    def refresh(self):
        self.list.clear()
        for item in reversed(self.browser.web_profile.history().items()):
            url = item.url().toString()
            if not url:
                continue
            row = QListWidgetItem(f"{item.title() or url}\n{url}")
            row.setData(Qt.ItemDataRole.UserRole, url)
            self.list.addItem(row)

    def open_item(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            self.browser.open_url(url)


class BookmarksPage(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 30)
        title = QLabel("Bookmarks")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        add = QPushButton("Save current page")
        add.setProperty("accent", True)
        add.clicked.connect(self.add_current)
        layout.addWidget(add)
        self.list = QListWidget()
        layout.addWidget(self.list, 1)
        self.refresh()
        self.list.itemDoubleClicked.connect(self.open_item)
        fade_in(self)

    def refresh(self):
        self.list.clear()
        for item in load_bookmarks():
            row = QListWidgetItem(f'{item.get("title", "")}\n{item.get("url", "")}')
            row.setData(Qt.ItemDataRole.UserRole, item.get("url", ""))
            self.list.addItem(row)

    def add_current(self):
        page = self.browser.current_browser()
        if page:
            add_bookmark(page.title(), page.url().toString())
            self.refresh()

    def open_item(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            self.browser.open_url(url)


class NotesPage(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.notes = load_notes()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 30)
        title = QLabel("Notes")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Write a note…")
        layout.addWidget(self.input)
        save = QPushButton("Save note")
        save.setProperty("accent", True)
        save.clicked.connect(self.add_note)
        layout.addWidget(save)
        self.list = QListWidget()
        layout.addWidget(self.list, 1)
        self.refresh()
        fade_in(self)

    def add_note(self):
        text = self.input.text().strip()
        if not text:
            return
        self.notes.insert(0, text)
        save_notes(self.notes)
        self.input.clear()
        self.refresh()

    def refresh(self):
        self.list.clear()
        for note in self.notes:
            self.list.addItem(note)


class DownloadsPage(QWidget):
    def __init__(self, browser):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 30)
        title = QLabel("Downloads")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.list = QListWidget()
        layout.addWidget(self.list, 1)
        try:
            for download in browser.web_profile.downloads():
                self.list.addItem(download.suggestedFileName())
        except Exception:
            self.list.addItem("No downloads yet")
        fade_in(self)


class SettingsPage(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 30)
        title = QLabel("Settings")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        sub = QLabel("Appearance and Orbit behavior")
        sub.setObjectName("muted")
        layout.addWidget(sub)
        row = QHBoxLayout()
        row.addWidget(QLabel("Theme"))
        self.theme = browser.theme_combo
        row.addWidget(self.theme)
        row.addStretch()
        layout.addLayout(row)
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Apply Orbit theme to websites"))
        self.theme_sites = QPushButton("ON" if browser.config.get("site_theming", True) else "OFF")
        self.theme_sites.setProperty("accent", browser.config.get("site_theming", True))
        row2.addWidget(self.theme_sites)
        row2.addStretch()
        layout.addLayout(row2)
        self.theme_sites.clicked.connect(self.toggle_site_theme)
        layout.addStretch()
        fade_in(self)

    def toggle_site_theme(self):
        enabled = not self.browser.config.get("site_theming", True)
        self.browser.config["site_theming"] = enabled
        self.theme_sites.setText("ON" if enabled else "OFF")
        self.theme_sites.setProperty("accent", enabled)
        self.theme_sites.style().unpolish(self.theme_sites)
        self.theme_sites.style().polish(self.theme_sites)
