from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QGridLayout, QWidget
from orbit_storage import add_bookmark, load_bookmarks, load_notes, save_notes

class HomePage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(45, 45, 45, 30)
        logo = QLabel("ORBIT")
        logo.setObjectName("logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)
        welcome = QLabel("Welcome")
        welcome.setObjectName("title")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome)
        sub = QLabel("Поиск, работа и развлечения — в одном браузере.")
        sub.setObjectName("muted")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)
        self.search = QLineEdit()
        self.search.setMinimumHeight(56)
        self.search.setPlaceholderText("Поиск в интернете или адрес сайта...")
        self.search.returnPressed.connect(lambda: self.window.navigate_text(self.search.text()))
        layout.addWidget(self.search)
        title = QLabel("Быстрый доступ")
        title.setObjectName("title")
        layout.addWidget(title)
        sites = [("Google", "https://google.com"), ("YouTube", "https://youtube.com"), ("GitHub", "https://github.com"), ("Discord", "https://discord.com"), ("Gmail", "https://mail.google.com"), ("Steam", "https://store.steampowered.com")]
        grid = QGridLayout()
        for i, (name, url) in enumerate(sites):
            button = QPushButton(name)
            button.setMinimumHeight(50)
            button.clicked.connect(lambda checked=False, u=url: self.window.open_url(u))
            grid.addWidget(button, i // 3, i % 3)
        layout.addLayout(grid)
        layout.addStretch()

class HistoryPage(QWidget):
    def __init__(self, window):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("История")
        title.setObjectName("title")
        layout.addWidget(title)
        self.list = QListWidget()
        layout.addWidget(self.list)
        for item in reversed(window.web_profile.history().items()):
            url = item.url().toString()
            if url:
                row = QListWidgetItem(f"{item.title() or url}\n{url}")
                row.setData(Qt.ItemDataRole.UserRole, url)
                self.list.addItem(row)
        self.list.itemDoubleClicked.connect(lambda item: window.open_url(item.data(Qt.ItemDataRole.UserRole)))

class BookmarksPage(QWidget):
    def __init__(self, window):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Закладки")
        title.setObjectName("title")
        layout.addWidget(title)
        add = QPushButton("Добавить текущую страницу")
        add.clicked.connect(self.add_current)
        layout.addWidget(add)
        self.list = QListWidget()
        layout.addWidget(self.list)
        self.window = window
        self.refresh()
        self.list.itemDoubleClicked.connect(lambda item: window.open_url(item.data(Qt.ItemDataRole.UserRole)))

    def refresh(self):
        self.list.clear()
        for item in load_bookmarks():
            row = QListWidgetItem(f"{item['title']}\n{item['url']}")
            row.setData(Qt.ItemDataRole.UserRole, item["url"])
            self.list.addItem(row)

    def add_current(self):
        browser = self.window.current_browser()
        if browser:
            add_bookmark(browser.title(), browser.url().toString())
            self.refresh()

class NotesPage(QWidget):
    def __init__(self, _window):
        super().__init__()
        self.notes = load_notes()
        layout = QVBoxLayout(self)
        title = QLabel("Orbit Notes")
        title.setObjectName("title")
        layout.addWidget(title)
        self.editor = QLineEdit()
        self.editor.setPlaceholderText("Новая заметка...")
        layout.addWidget(self.editor)
        add = QPushButton("Сохранить заметку")
        add.clicked.connect(self.add_note)
        layout.addWidget(add)
        self.list = QListWidget()
        layout.addWidget(self.list)
        self.refresh()

    def add_note(self):
        text = self.editor.text().strip()
        if text:
            self.notes.insert(0, text)
            save_notes(self.notes)
            self.editor.clear()
            self.refresh()

    def refresh(self):
        self.list.clear()
        self.list.addItems(self.notes)

class DownloadsPage(QWidget):
    def __init__(self, window):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Загрузки")
        title.setObjectName("title")
        layout.addWidget(title)
        self.list = QListWidget()
        layout.addWidget(self.list)
        try:
            for download in window.web_profile.downloads():
                self.list.addItem(download.suggestedFileName())
        except Exception:
            self.list.addItem("Загрузки появятся здесь")

class SettingsPage(QWidget):
    def __init__(self, window):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Настройки")
        title.setObjectName("title")
        layout.addWidget(title)
        label = QLabel("Тема интерфейса меняется сверху в панели Orbit.")
        layout.addWidget(label)
        layout.addStretch()
