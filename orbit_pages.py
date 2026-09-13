from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
QFrame,
QGridLayout,
QHBoxLayout,
QLabel,
QLineEdit,
QListWidget,
QListWidgetItem,
QPushButton,
QVBoxLayout,
QWidget,
)

from orbit_storage import (
add_bookmark,
load_bookmarks,
load_notes,
save_notes,
)

class HomePage(QWidget):

```
def __init__(
    self,
    window,
):
    super().__init__()

    self.window = window

    layout = QVBoxLayout(
        self
    )

    layout.setContentsMargins(
        45,
        45,
        45,
        30,
    )

    layout.setSpacing(
        18
    )

    logo = QLabel(
        "ORBIT"
    )

    logo.setObjectName(
        "logo"
    )

    logo.setAlignment(
        Qt.AlignmentFlag.AlignCenter
    )

    layout.addWidget(
        logo
    )

    welcome = QLabel(
        "Welcome"
    )

    welcome.setObjectName(
        "title"
    )

    welcome.setAlignment(
        Qt.AlignmentFlag.AlignCenter
    )

    layout.addWidget(
        welcome
    )

    subtitle = QLabel(
        "Поиск, работа и развлечения — в одном браузере."
    )

    subtitle.setObjectName(
        "muted"
    )

    subtitle.setAlignment(
        Qt.AlignmentFlag.AlignCenter
    )

    layout.addWidget(
        subtitle
    )

    self.search = QLineEdit()

    self.search.setMinimumHeight(
        56
    )

    self.search.setPlaceholderText(
        "Поиск в интернете или адрес сайта..."
    )

    layout.addWidget(
        self.search
    )

    self.search.returnPressed.connect(
        self.search_web
    )

    quick_title = QLabel(
        "Быстрый доступ"
    )

    quick_title.setObjectName(
        "section"
    )

    layout.addWidget(
        quick_title
    )

    sites = [
        ("Google", "https://google.com"),
        ("YouTube", "https://youtube.com"),
        ("GitHub", "https://github.com"),
        ("Discord", "https://discord.com"),
        ("Gmail", "https://mail.google.com"),
        ("Steam", "https://store.steampowered.com"),
    ]

    grid = QGridLayout()

    for index, (name, url) in enumerate(
        sites
    ):
        button = QPushButton(
            name
        )

        button.setMinimumHeight(
            48
        )

        button.clicked.connect(
            lambda checked=False, target=url:
            self.window.open_url(
                target
            )
        )

        grid.addWidget(
            button,
            index // 3,
            index % 3,
        )

    layout.addLayout(
        grid
    )

    layout.addStretch()

def search_web(self):
    text = self.search.text().strip()

    if not text:
        return

    self.window.navigate_text(
        text
    )
```

class HistoryPage(QWidget):

```
def __init__(
    self,
    window,
):
    super().__init__()

    self.window = window

    layout = QVBoxLayout(
        self
    )

    title = QLabel(
        "История"
    )

    title.setObjectName(
        "title"
    )

    layout.addWidget(
        title
    )

    self.list = QListWidget()

    layout.addWidget(
        self.list
    )

    self.refresh()

def refresh(self):
    self.list.clear()

    history = (
        self.window.web_profile.history()
        .items()
    )

    for item in reversed(
        history
    ):
        url = item.url().toString()

        if not url:
            continue

        title = item.title() or url

        list_item = QListWidgetItem(
            f"{title}\n{url}"
        )

        list_item.setData(
            Qt.ItemDataRole.UserRole,
            url,
        )

        self.list.addItem(
            list_item
        )

    self.list.itemDoubleClicked.connect(
        self.open_item
    )

def open_item(
    self,
    item,
):
    url = item.data(
        Qt.ItemDataRole.UserRole
    )

    if url:
        self.window.open_url(
            url
        )
```

class BookmarksPage(QWidget):

```
def __init__(
    self,
    window,
):
    super().__init__()

    self.window = window

    layout = QVBoxLayout(
        self
    )

    title = QLabel(
        "Закладки"
    )

    title.setObjectName(
        "title"
    )

    layout.addWidget(
        title
    )

    add = QPushButton(
        "Добавить текущую страницу"
    )

    add.clicked.connect(
        self.add_current
    )

    layout.addWidget(
        add
    )

    self.list = QListWidget()

    layout.addWidget(
        self.list
    )

    self.list.itemDoubleClicked.connect(
        self.open_item
    )

    self.refresh()

def refresh(self):
    self.list.clear()

    for item in load_bookmarks():
        row = QListWidgetItem(
            f'{item["title"]}\n{item["url"]}'
        )

        row.setData(
            Qt.ItemDataRole.UserRole,
            item["url"],
        )

        self.list.addItem(
            row
        )

def add_current(self):
    browser = self.window.current_browser()

    if not browser:
        return

    url = browser.url().toString()

    if not url:
        return

    add_bookmark(
        browser.title(),
        url,
    )

    self.refresh()

def open_item(
    self,
    item,
):
    url = item.data(
        Qt.ItemDataRole.UserRole
    )

    if url:
        self.window.open_url(
            url
        )
```

class NotesPage(QWidget):

```
def __init__(
    self,
    window,
):
    super().__init__()

    self.window = window
    self.notes = load_notes()

    layout = QVBoxLayout(
        self
    )

    title = QLabel(
        "Orbit Notes"
    )

    title.setObjectName(
        "title"
    )

    layout.addWidget(
        title
    )

    self.editor = QLineEdit()

    self.editor.setPlaceholderText(
        "Новая заметка..."
    )

    layout.addWidget(
        self.editor
    )

    add = QPushButton(
        "Сохранить заметку"
    )

    add.clicked.connect(
        self.add_note
    )

    layout.addWidget(
        add
    )

    self.list = QListWidget()

    layout.addWidget(
        self.list
    )

    self.refresh()

def add_note(self):
    text = self.editor.text().strip()

    if not text:
        return

    self.notes.insert(
        0,
        text,
    )

    save_notes(
        self.notes
    )

    self.editor.clear()

    self.refresh()

def refresh(self):
    self.list.clear()

    for note in self.notes:
        self.list.addItem(
            note
        )
```

class DownloadsPage(QWidget):

```
def __init__(
    self,
    window,
):
    super().__init__()

    self.window = window

    layout = QVBoxLayout(
        self
    )

    title = QLabel(
        "Загрузки"
    )

    title.setObjectName(
        "title"
    )

    layout.addWidget(
        title
    )

    self.list = QListWidget()

    layout.addWidget(
        self.list
    )

    self.refresh()

def refresh(self):
    self.list.clear()

    downloads = self.window.web_profile.downloads()

    for download in downloads:
        item = QListWidgetItem(
            download.suggestedFileName()
        )

        self.list.addItem(
            item
        )
```

class SettingsPage(QWidget):

```
def __init__(
    self,
    window,
):
    super().__init__()

    self.window = window

    layout = QVBoxLayout(
        self
    )

    title = QLabel(
        "Настройки"
    )

    title.setObjectName(
        "title"
    )

    layout.addWidget(
        title
    )

    theme_label = QLabel(
        "Тема интерфейса"
    )

    layout.addWidget(
        theme_label
    )

    self.theme = self.window.theme_combo

    layout.addWidget(
        self.theme
    )

    animation = QPushButton(
        "Плавные анимации: ON"
    )

    animation.clicked.connect(
        self.toggle_animation
    )

    layout.addWidget(
        animation
    )

    layout.addStretch()

def toggle_animation(self):
    current = self.window.config.get(
        "animations",
        True,
    )

    self.window.config["animations"] = not current
```
