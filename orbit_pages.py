from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QGridLayout,
    QFrame,
    QWidget,
)

from orbit_storage import (
    add_bookmark,
    load_bookmarks,
    load_notes,
    save_notes,
    save_config,
)
from orbit_ui import THEMES


class HomePage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 70, 40, 60)
        layout.setSpacing(14)

        layout.addStretch(2)

        logo = QLabel("ORBIT")
        logo.setObjectName("orbitLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        welcome = QLabel("Welcome")
        welcome.setObjectName("homeWelcome")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(welcome)

        search = QLineEdit()
        search.setObjectName("address")
        search.setMinimumHeight(58)
        search.setMaximumWidth(760)
        search.setPlaceholderText("Поиск в интернете или введите адрес…")
        search.returnPressed.connect(lambda: self.window.navigate_text(search.text()))
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(search)
        row.addStretch()
        layout.addLayout(row)

        shortcuts = QHBoxLayout()
        shortcuts.setSpacing(3)
        shortcuts.addStretch()
        for title, callback in [
            ("История", self.window.open_history),
            ("Закладки", self.window.open_bookmarks),
            ("Загрузки", self.window.open_downloads),
            ("Notes", self.window.open_notes),
            ("Профиль", self.window.open_profile),
            ("Настройки", self.window.open_settings),
        ]:
            button = QPushButton(title)
            button.setObjectName("homeShortcut")
            button.clicked.connect(callback)
            shortcuts.addWidget(button)
        shortcuts.addStretch()
        layout.addLayout(shortcuts)
        layout.addStretch(3)


class HistoryPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(42, 34, 42, 34)
        layout.setSpacing(12)

        title = QLabel("История")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel("Недавно открытые страницы")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)

        self.list = QListWidget()
        layout.addWidget(self.list, 1)
        self.refresh()
        self.list.itemDoubleClicked.connect(self.open_item)

    def refresh(self):
        self.list.clear()
        try:
            items = self.window.web_profile.history().items()
        except Exception:
            items = []
        for item in reversed(items):
            url = item.url().toString()
            if not url:
                continue
            row = QListWidgetItem(f"{item.title() or url}\n{url}")
            row.setData(Qt.ItemDataRole.UserRole, url)
            self.list.addItem(row)
        if self.list.count() == 0:
            self.list.addItem("История пока пуста")

    def open_item(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            self.window.open_url(url)


class BookmarksPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(42, 34, 42, 34)
        layout.setSpacing(12)

        title = QLabel("Закладки")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        row = QHBoxLayout()
        add = QPushButton("Добавить текущую")
        add.setProperty("accent", True)
        add.clicked.connect(self.add_current)
        row.addWidget(add)
        refresh = QPushButton("Обновить")
        refresh.clicked.connect(self.refresh)
        row.addWidget(refresh)
        row.addStretch()
        layout.addLayout(row)

        self.list = QListWidget()
        layout.addWidget(self.list, 1)
        self.list.itemDoubleClicked.connect(self.open_item)
        self.refresh()

    def refresh(self):
        self.list.clear()
        for item in load_bookmarks():
            url = item.get("url", "")
            if not url:
                continue
            row = QListWidgetItem(f"{item.get('title', url)}\n{url}")
            row.setData(Qt.ItemDataRole.UserRole, url)
            self.list.addItem(row)
        if self.list.count() == 0:
            self.list.addItem("Закладок пока нет")

    def add_current(self):
        browser = self.window.current_browser()
        if browser:
            add_bookmark(browser.title(), browser.url().toString())
            self.refresh()

    def open_item(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            self.window.open_url(url)


class NotesPage(QWidget):
    def __init__(self, _window):
        super().__init__()
        self.notes = load_notes()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(42, 34, 42, 34)
        layout.setSpacing(12)

        title = QLabel("Notes")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        row = QHBoxLayout()
        self.editor = QLineEdit()
        self.editor.setPlaceholderText("Новая заметка…")
        row.addWidget(self.editor, 1)
        add = QPushButton("Сохранить")
        add.setProperty("accent", True)
        add.clicked.connect(self.add_note)
        row.addWidget(add)
        layout.addLayout(row)

        self.list = QListWidget()
        layout.addWidget(self.list, 1)
        self.refresh()

    def add_note(self):
        text = self.editor.text().strip()
        if not text:
            return
        self.notes.insert(0, text)
        save_notes(self.notes)
        self.editor.clear()
        self.refresh()

    def refresh(self):
        self.list.clear()
        self.list.addItems(self.notes)
        if not self.notes:
            self.list.addItem("Заметок пока нет")


class DownloadsPage(QWidget):
    def __init__(self, window):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(42, 34, 42, 34)
        layout.setSpacing(12)
        title = QLabel("Загрузки")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.list = QListWidget()
        layout.addWidget(self.list, 1)
        try:
            downloads = window.web_profile.downloads()
        except Exception:
            downloads = []
        for download in downloads:
            self.list.addItem(download.suggestedFileName())
        if self.list.count() == 0:
            self.list.addItem("Загрузок пока нет")


class SettingsPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(42, 34, 42, 34)
        layout.setSpacing(18)

        title = QLabel("Настройки")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        appearance_card = QFrame()
        appearance_card.setObjectName("settingsCard")
        card = QVBoxLayout(appearance_card)
        card.setContentsMargins(24, 22, 24, 22)
        card.setSpacing(14)

        heading = QLabel("Внешний вид")
        heading.setObjectName("sectionTitle")
        card.addWidget(heading)

        row = QHBoxLayout()
        row.addWidget(QLabel("Тема Orbit"))
        self.theme = QComboBox()
        self.theme.addItems(THEMES.keys())
        self.theme.setCurrentText(window.current_theme)
        self.theme.currentTextChanged.connect(window.change_theme)
        row.addWidget(self.theme)
        row.addStretch()
        card.addLayout(row)

        self.site_theme = QCheckBox("Применять тему Orbit к сайтам")
        self.site_theme.setChecked(bool(window.config.get("site_theme_enabled", True)))
        self.site_theme.stateChanged.connect(self.save_site_theme)
        card.addWidget(self.site_theme)

        hint = QLabel("Тёмная тема применяется к интерфейсу Orbit и, где позволяет сайт, к содержимому страниц.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        card.addWidget(hint)

        layout.addWidget(appearance_card)
        layout.addStretch()

    def save_site_theme(self, state):
        self.window.config["site_theme_enabled"] = bool(state)
        save_config(self.window.config)
        self.window.apply_site_theme_to_all()


class ProfilePage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.build()

    def build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(42, 34, 42, 34)
        layout.setSpacing(18)

        top = QFrame()
        top.setObjectName("profileCard")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(24, 24, 24, 24)

        avatar = QLabel()
        avatar.setText((self.window.user.get("display_name") or self.window.user.get("username", "O"))[0].upper())
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(78, 78)
        avatar.setStyleSheet("font-size:32px;font-weight:800;border-radius:39px;background:#252733;")
        top_layout.addWidget(avatar)

        details = QVBoxLayout()
        name = self.window.user.get("display_name") or self.window.user.get("username", "User")
        username = self.window.user.get("username", "user")
        details.addWidget(QLabel(f"<b style='font-size:24px'>{name}</b>"))
        details.addWidget(QLabel(f"@{username}"))
        role = self.window.user.get("role", "user")
        badge_text = "👑 Founder · Creator of Orbit" if role == "founder" else self.window.user.get("title", "Explorer")
        badge = QLabel(badge_text)
        badge.setObjectName("badge")
        details.addWidget(badge)
        top_layout.addLayout(details)
        top_layout.addStretch()
        layout.addWidget(top)

        xp = int(self.window.user.get("xp", 0))
        level = xp // 500 + 1
        xp_now = xp % 500

        level_row = QHBoxLayout()
        level_row.addWidget(QLabel(f"Level {level}"))
        level_row.addStretch()
        level_row.addWidget(QLabel(f"{xp} XP"))
        layout.addLayout(level_row)

        progress = QProgressBar()
        progress.setRange(0, 500)
        progress.setValue(xp_now)
        layout.addWidget(progress)

        stats = QFrame()
        stats.setObjectName("contentCard")
        stats_layout = QGridLayout(stats)
        stats_layout.setContentsMargins(20, 18, 20, 18)
        for col, (label, value) in enumerate([
            ("Вкладки", "—"),
            ("Заметки", str(len(load_notes()))),
            ("Закладки", str(len(load_bookmarks()))),
        ]):
            stats_layout.addWidget(QLabel(label), 0, col)
            value_label = QLabel(value)
            value_label.setStyleSheet("font-size:20px;font-weight:700;")
            stats_layout.addWidget(value_label, 1, col)
        layout.addWidget(stats)

        achievements = QFrame()
        achievements.setObjectName("contentCard")
        a_layout = QVBoxLayout(achievements)
        a_layout.setContentsMargins(20, 18, 20, 18)
        a_layout.addWidget(QLabel("Ачивки"))
        items = [
            ("🚀", "First Flight", 100),
            ("🌌", "Explorer", 250),
            ("⚡", "Power User", 500),
            ("✦", "Creator", 750),
            ("👑", "Founder", 1000),
        ]
        for icon, title, required in items:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{icon} {title}"))
            row.addStretch()
            row.addWidget(QLabel("Разблокировано" if xp >= required or (title == "Founder" and role == "founder") else "Заблокировано"))
            a_layout.addLayout(row)
        layout.addWidget(achievements)
        layout.addStretch()
