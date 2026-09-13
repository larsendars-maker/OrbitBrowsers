from urllib.parse import quote_plus, unquote_plus
import re

import requests
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from orbit_storage import (
    APP_DIR,
    AVATAR_FILE,
    add_bookmark,
    add_shortcut,
    load_bookmarks,
    load_notes,
    load_shortcuts,
    remove_shortcut,
    save_notes,
    save_shortcuts,
)
from orbit_ui import THEMES, fade_in, tr


class AddShortcutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить сайт")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        title = QLabel("Добавить сайт на главную")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        form = QFormLayout()
        self.name = QLineEdit()
        self.name.setPlaceholderText("Например: Discord")
        self.url = QLineEdit()
        self.url.setPlaceholderText("https://discord.com")
        form.addRow("Название", self.name)
        form.addRow("Адрес", self.url)
        layout.addLayout(form)
        row = QHBoxLayout()
        cancel = QPushButton("Отмена")
        save = QPushButton("Добавить")
        save.setProperty("accent", True)
        row.addWidget(cancel)
        row.addWidget(save)
        layout.addLayout(row)
        cancel.clicked.connect(self.reject)
        save.clicked.connect(self.accept)

    def values(self):
        name = self.name.text().strip()
        url = self.url.text().strip()
        if url and not url.startswith(("http://", "https://", "orbit://")):
            url = "https://" + url
        return name, url


class WeatherDialog(QDialog):
    def __init__(self, parent=None, current_city="Москва"):
        super().__init__(parent)
        self.setWindowTitle("Orbit Weather")
        self.setMinimumSize(560, 500)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Погода по всему миру")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel("Введите город, регион или страну — Orbit найдёт ближайшие погодные точки.")
        subtitle.setObjectName("homepageSub")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        row = QHBoxLayout()
        self.query = QLineEdit(current_city)
        self.query.setPlaceholderText("Например: Москва, Berlin, New York, Токио")
        search = QPushButton("Найти")
        search.setProperty("accent", True)
        row.addWidget(self.query, 1)
        row.addWidget(search)
        layout.addLayout(row)

        self.results = QListWidget()
        layout.addWidget(self.results, 1)

        self.status = QLabel("")
        self.status.setObjectName("homepageSub")
        layout.addWidget(self.status)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Закрыть")
        apply_btn = QPushButton("Выбрать город")
        apply_btn.setProperty("accent", True)
        buttons.addWidget(cancel)
        buttons.addWidget(apply_btn)
        layout.addLayout(buttons)

        search.clicked.connect(self.search_city)
        self.query.returnPressed.connect(self.search_city)
        cancel.clicked.connect(self.reject)
        apply_btn.clicked.connect(self.accept_selection)
        self.results.itemDoubleClicked.connect(lambda _: self.accept_selection())
        self.selected = None
        self.search_city()

    def search_city(self):
        query = self.query.text().strip()
        if not query:
            return
        self.status.setText("Ищем города…")
        self.results.clear()
        try:
            response = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": query, "count": 10, "language": "ru", "format": "json"},
                timeout=8,
            )
            response.raise_for_status()
            results = response.json().get("results") or []
        except Exception as exc:
            self.status.setText(f"Не удалось найти город: {exc}")
            return

        if not results:
            self.status.setText("Ничего не найдено. Попробуйте другое написание.")
            return

        for result in results:
            city = result.get("name") or "Неизвестный город"
            country = result.get("country") or result.get("country_code") or ""
            admin = result.get("admin1") or ""
            label = " · ".join([part for part in [city, admin, country] if part])
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, {
                "name": city,
                "country": country,
                "admin1": admin,
                "latitude": result.get("latitude"),
                "longitude": result.get("longitude"),
                "timezone": result.get("timezone", "auto"),
            })
            self.results.addItem(item)
        self.results.setCurrentRow(0)
        self.status.setText(f"Найдено вариантов: {len(results)}")

    def accept_selection(self):
        item = self.results.currentItem()
        if not item:
            return
        self.selected = item.data(Qt.ItemDataRole.UserRole)
        self.accept()


class HomePage(QWidget):
    weatherChanged = Signal(str)

    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.setObjectName("homePage")
        self.weather_data = None
        self.build()
        fade_in(self, 220)
        self.refresh_weather()

    def lang(self, key):
        return tr(self.browser.config.get("language", "ru"), key)

    def build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(54, 20, 54, 18)
        outer.setSpacing(0)

        outer.addStretch(1)

        center = QVBoxLayout()
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.setSpacing(4)

        logo = QLabel("Orbit")
        logo.setObjectName("homeLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.addWidget(logo)
        self.logo_label = logo

        welcome = QLabel(self.lang("welcome"))
        welcome.setObjectName("homeWelcome")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.addWidget(welcome)
        self.welcome_label = welcome

        subtitle = QLabel(self.lang("future"))
        subtitle.setObjectName("homepageSub")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.addWidget(subtitle)

        center.addSpacing(10)

        search_shell = QFrame()
        search_shell.setObjectName("mainSearch")
        search_shell.setMaximumWidth(620)
        search_shell.setMinimumHeight(54)
        search_row = QHBoxLayout(search_shell)
        search_row.setContentsMargins(10, 5, 8, 5)
        search_row.setSpacing(5)

        icon = QLabel("⌕")
        icon.setObjectName("searchIcon")
        search_row.addWidget(icon)

        self.search = QLineEdit()
        self.search.setMinimumHeight(40)
        self.search.setPlaceholderText(self.lang("search"))
        search_row.addWidget(self.search, 1)

        engine_name = {
            "google": "Google", "bing": "Bing", "duckduckgo": "DuckDuckGo", "orbit": "Orbit"
        }.get(self.browser.config.get("search_engine", "google"), "Google")
        self.engine_hint = QPushButton(engine_name)
        self.engine_hint.setObjectName("searchUtility")
        self.engine_hint.setToolTip("Выбрать поисковую систему / Choose search engine")
        self.engine_hint.clicked.connect(self.browser.open_settings)
        search_row.addWidget(self.engine_hint)

        go = QPushButton("→")
        go.setObjectName("searchButton")
        go.setFixedSize(40, 40)
        go.setProperty("accent", True)
        search_row.addWidget(go)

        center.addWidget(search_shell, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.search.returnPressed.connect(self.run_search)
        go.clicked.connect(self.run_search)

        center.addSpacing(10)

        quick_shell = QFrame()
        quick_shell.setObjectName("quickShell")
        quick_shell.setMaximumWidth(620)
        quick_row = QHBoxLayout(quick_shell)
        quick_row.setContentsMargins(8, 4, 8, 4)
        quick_row.setSpacing(8)

        title = QLabel(self.lang("quick"))
        title.setObjectName("homepageSection")
        quick_row.addWidget(title)
        self.quick_title = title
        quick_row.addStretch()
        add = QPushButton("＋  " + self.lang("add"))
        add.setObjectName("addShortcut")
        add.clicked.connect(self.add_site)
        quick_row.addWidget(add)
        self.add_shortcut_button = add

        center.addWidget(quick_shell, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.shortcut_row = QHBoxLayout()
        self.shortcut_row.setSpacing(12)
        self.shortcut_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        center.addLayout(self.shortcut_row)
        self.refresh_shortcuts()

        outer.addLayout(center)
        outer.addStretch(1)

        bottom = QHBoxLayout()
        self.weather_button = QPushButton("◌  " + self.lang("weather"))
        self.weather_button.setObjectName("weatherSearch")
        self.weather_button.clicked.connect(self.open_weather_dialog)
        bottom.addWidget(self.weather_button)
        bottom.addStretch()
        outer.addLayout(bottom)

    def refresh_weather(self):
        """Обновляет погодный блок по сохранённому городу и уведомляет боковую панель."""
        language = self.browser.config.get("language", "ru")
        city = (self.browser.config.get("weather_city") or "Москва").strip()
        country = (self.browser.config.get("weather_country") or "").strip()
        lat = self.browser.config.get("weather_latitude")
        lon = self.browser.config.get("weather_longitude")

        self.weather_button.setText("◌  " + city)
        self.weather_button.setToolTip("Открыть выбор города" if language == "ru" else "Change weather city")

        try:
            if lat is None or lon is None:
                response = requests.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={
                        "name": city,
                        "count": 1,
                        "language": "ru" if language == "ru" else "en",
                        "format": "json",
                    },
                    timeout=6,
                )
                response.raise_for_status()
                result = (response.json().get("results") or [None])[0]
                if result:
                    lat = result.get("latitude")
                    lon = result.get("longitude")
                    city = result.get("name") or city
                    country = result.get("country") or country

            if lat is None or lon is None:
                raise ValueError("координаты города не найдены")

            response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
                    "timezone": "auto",
                },
                timeout=8,
            )
            response.raise_for_status()
            current = response.json().get("current", {})
            temp = current.get("temperature_2m")
            feels = current.get("apparent_temperature")
            humidity = current.get("relative_humidity_2m")
            wind = current.get("wind_speed_10m")
            code = current.get("weather_code")

            conditions_ru = {
                0: "Ясно", 1: "Преимущественно ясно", 2: "Переменная облачность", 3: "Пасмурно",
                45: "Туман", 48: "Изморозь", 51: "Морось", 53: "Морось", 55: "Сильная морось",
                61: "Небольшой дождь", 63: "Дождь", 65: "Сильный дождь", 71: "Небольшой снег",
                73: "Снег", 75: "Сильный снег", 80: "Ливни", 81: "Сильные ливни",
                82: "Очень сильные ливни", 95: "Гроза", 96: "Гроза с градом", 99: "Сильная гроза с градом",
            }
            conditions_en = {
                0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Rime fog",
                51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle", 61: "Light rain", 63: "Rain",
                65: "Heavy rain", 71: "Light snow", 73: "Snow", 75: "Heavy snow", 80: "Rain showers",
                81: "Heavy rain showers", 82: "Violent rain showers", 95: "Thunderstorm",
                96: "Thunderstorm with hail", 99: "Strong thunderstorm with hail",
            }
            condition = (conditions_ru if language == "ru" else conditions_en).get(code, "—")

            if temp is None:
                raise ValueError("температура недоступна")

            self.weather_data = {
                "city": city,
                "country": country,
                "temperature": temp,
                "apparent": feels,
                "humidity": humidity,
                "wind": wind,
                "condition": condition,
            }

            self.browser.config.update({
                "weather_city": city,
                "weather_country": country,
                "weather_latitude": lat,
                "weather_longitude": lon,
            })
            from orbit_storage import save_config
            save_config(self.browser.config)

            self.weather_button.setText(f"◌  {city} · {temp:.1f}°C")
            details = [condition]
            if feels is not None:
                details.append(f"ощущается {feels:.1f}°C" if language == "ru" else f"feels {feels:.1f}°C")
            if humidity is not None:
                details.append(f"влажность {humidity}%" if language == "ru" else f"humidity {humidity}%")
            if wind is not None:
                details.append(f"ветер {wind:.1f} км/ч" if language == "ru" else f"wind {wind:.1f} km/h")
            self.weather_button.setToolTip(" · ".join(details))
            self.weatherChanged.emit(self.weather_button.text())
        except Exception:
            self.weather_button.setText("◌  " + city)
            self.weather_button.setToolTip(
                "Погода временно недоступна" if language == "ru" else "Weather temporarily unavailable"
            )
            self.weatherChanged.emit(self.weather_button.text())

    def apply_language(self):
        language = self.browser.config.get("language", "ru")
        if hasattr(self, "welcome_label"):
            self.welcome_label.setText(tr(language, "welcome"))
        if hasattr(self, "search"):
            self.search.setPlaceholderText(tr(language, "search"))
        if hasattr(self, "quick_title"):
            self.quick_title.setText(tr(language, "quick"))
        if hasattr(self, "add_shortcut_button"):
            self.add_shortcut_button.setText("＋  " + tr(language, "add"))
        if hasattr(self, "weather_button"):
            current = self.browser.config.get("weather_city", "") or tr(language, "weather")
            self.weather_button.setText("◌  " + current)
        if hasattr(self, "engine_hint"):
            name = {"google":"Google", "bing":"Bing", "duckduckgo":"DuckDuckGo", "orbit":"Orbit"}.get(self.browser.config.get("search_engine", "google"), "Google")
            self.engine_hint.setText(name)

    def clear_shortcuts(self):
        while self.shortcut_row.count():
            item = self.shortcut_row.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def icon_for(self, item):
        title = item.get("title", "Сайт").lower()
        if "youtube" in title:
            return "▶", "#ff3b4f"
        if "discord" in title:
            return "◉", "#6474ef"
        if "spotify" in title:
            return "♪", "#1ed760"
        if "github" in title:
            return "◒", "#2c2c35"
        if "telegram" in title:
            return "➤", "#36a9e8"
        if "twitch" in title:
            return "ϟ", "#8b4cff"
        return item.get("icon", "↗"), "#7657ff"

    def refresh_shortcuts(self):
        self.clear_shortcuts()
        shortcuts = load_shortcuts()
        for item in shortcuts[:6]:
            wrapper = QFrame()
            wrapper.setObjectName("shortcutItem")
            wrapper.setFixedWidth(72)
            box = QVBoxLayout(wrapper)
            box.setContentsMargins(1, 0, 1, 0)
            box.setSpacing(4)
            box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_text, icon_color = self.icon_for(item)
            icon = QLabel(icon_text)
            icon.setObjectName("shortcutCircle")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setStyleSheet(f"background:{icon_color}; color:white; border-radius:28px;")
            box.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)
            name = QLabel(item.get("title", "Сайт"))
            name.setObjectName("shortcutName")
            name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name.setWordWrap(True)
            box.addWidget(name)
            wrapper.setToolTip(item.get("url", ""))
            wrapper.mousePressEvent = lambda event, u=item.get("url", ""): self.browser.open_url(u)
            self.shortcut_row.addWidget(wrapper)

        add_wrapper = QFrame()
        add_wrapper.setObjectName("shortcutItem")
        add_wrapper.setFixedWidth(72)
        add_box = QVBoxLayout(add_wrapper)
        add_box.setContentsMargins(1, 0, 1, 0)
        add_box.setSpacing(4)
        add_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plus = QLabel("+")
        plus.setObjectName("shortcutCircle")
        plus.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plus.setStyleSheet("background:rgba(80,64,110,70); color:#d8c9e7; border:1px solid rgba(167,124,255,80); border-radius:28px;")
        add_box.addWidget(plus, alignment=Qt.AlignmentFlag.AlignCenter)
        add_label = QLabel(tr(self.browser.config.get("language", "ru"), "add"))
        add_label.setObjectName("shortcutName")
        add_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        add_box.addWidget(add_label)
        add_wrapper.mousePressEvent = lambda event: self.add_site()
        self.shortcut_row.addWidget(add_wrapper)

    def add_site(self):
        dialog = AddShortcutDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        title, url = dialog.values()
        if not title or not url:
            return
        add_shortcut(title, url)
        self.refresh_shortcuts()

    def run_search(self):
        self.browser.navigate_text(self.search.text().strip())

    def open_weather_dialog(self):
        current = self.browser.config.get("weather_city", "Москва")
        dialog = WeatherDialog(self, current)
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.selected:
            return
        data = dialog.selected
        self.browser.config["weather_city"] = data["name"]
        self.browser.config["weather_country"] = data.get("country", "")
        self.browser.config["weather_latitude"] = data.get("latitude")
        self.browser.config["weather_longitude"] = data.get("longitude")
        from orbit_storage import save_config
        save_config(self.browser.config)
        self.refresh_weather()


class SearchPage(QWidget):
    def __init__(self, browser, query=""):
        super().__init__()
        self.browser = browser
        self.query = query
        layout = QVBoxLayout(self)
        layout.setContentsMargins(70, 45, 70, 40)
        layout.setSpacing(18)
        shell = QFrame()
        shell.setObjectName("searchShell")
        row = QHBoxLayout(shell)
        row.setContentsMargins(8, 2, 8, 2)
        self.input = QLineEdit(query)
        row.addWidget(self.input, 1)
        go = QPushButton("Поиск")
        go.setProperty("accent", True)
        row.addWidget(go)
        layout.addWidget(shell)
        self.results = QListWidget()
        layout.addWidget(self.results, 1)
        go.clicked.connect(self.run_search)
        self.input.returnPressed.connect(self.run_search)
        self.results.itemDoubleClicked.connect(self.open_item)
        if query:
            self.run_search()
        else:
            self.results.addItem(QListWidgetItem("Введите запрос, чтобы начать поиск в Orbit."))
        fade_in(self)

    def run_search(self):
        query = self.input.text().strip()
        if not query:
            return
        self.browser.navigate_text(query)

    def open_item(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url:
            self.browser.open_url(url)


class HistoryPage(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 40, 50, 35)
        title = QLabel("История")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
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
        layout.setContentsMargins(50, 40, 50, 35)
        title = QLabel("Закладки")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        add = QPushButton("Сохранить текущую страницу")
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
        self.notes = load_notes()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 40, 50, 35)
        title = QLabel("Заметки")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Новая заметка…")
        layout.addWidget(self.input)
        save = QPushButton("Сохранить")
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
        layout.setContentsMargins(50, 40, 50, 35)
        title = QLabel("Загрузки")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.list = QListWidget()
        layout.addWidget(self.list, 1)
        try:
            downloads = browser.web_profile.downloads()
            for item in downloads:
                self.list.addItem(item.suggestedFileName())
        except Exception:
            self.list.addItem("Загрузок пока нет")
        fade_in(self)


class ProfilePage(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.build()
        fade_in(self, 240)

    def avatar_path(self):
        path = self.browser.config.get("avatar_path", "")
        return path if path and __import__("os").path.exists(path) else str(AVATAR_FILE) if AVATAR_FILE.exists() else ""

    def build_avatar(self):
        self.avatar = QLabel()
        self.avatar.setObjectName("profileAvatar")
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setFixedSize(96, 96)
        self.refresh_avatar()
        return self.avatar

    def refresh_avatar(self):
        path = self.avatar_path()
        if path:
            pixmap = __import__("PySide6.QtGui", fromlist=["QPixmap"]).QPixmap(path)
            if not pixmap.isNull():
                self.avatar.setPixmap(pixmap.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
                return
        name = self.browser.user.get("display_name") or self.browser.user.get("username", "O")
        self.avatar.setText(name[0].upper())

    def build(self):
        user = self.browser.user
        layout = QVBoxLayout(self)
        layout.setContentsMargins(64, 42, 64, 50)
        layout.setSpacing(18)

        top = QHBoxLayout()
        top.setSpacing(16)
        top.addWidget(self.build_avatar())

        info = QVBoxLayout()
        name = user.get("display_name") or user.get("username", "User")
        name_label = QLabel(name)
        name_label.setObjectName("profileName")
        info.addWidget(name_label)
        handle = QLabel("@" + user.get("username", "user"))
        handle.setObjectName("muted")
        info.addWidget(handle)
        role = user.get("role", "user")
        role_label = QLabel("Создатель Orbit" if role == "founder" else (user.get("title", "Explorer") or "Explorer"))
        role_label.setObjectName("founderBadge" if role == "founder" else "muted")
        info.addWidget(role_label)
        top.addLayout(info)
        top.addStretch()

        edit = QPushButton("Настроить профиль")
        edit.setProperty("accent", True)
        edit.clicked.connect(self.edit_profile)
        top.addWidget(edit, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)

        bio = user.get("bio", "") or "Добро пожаловать в Orbit. Здесь можно настроить профиль, тему и фотографию."
        bio_label = QLabel(bio)
        bio_label.setObjectName("profileBio")
        bio_label.setWordWrap(True)
        layout.addWidget(bio_label)

        xp = int(user.get("xp", 0))
        level = xp // 500 + 1
        progress = xp % 500
        stats = QHBoxLayout()
        stats.setSpacing(14)
        for value, label in [(str(level), "Уровень"), (str(xp), "XP"), ("Создатель" if role == "founder" else "Участник", "Статус")]:
            card = QFrame()
            card.setObjectName("profileStat")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 14, 16, 14)
            val = QLabel(value)
            val.setObjectName("profileStatValue")
            lab = QLabel(label)
            lab.setObjectName("muted")
            cl.addWidget(val)
            cl.addWidget(lab)
            stats.addWidget(card)
        layout.addLayout(stats)

        progress_label = QLabel(f"{progress}/500 XP до следующего уровня")
        progress_label.setObjectName("muted")
        layout.addWidget(progress_label)

        section = QLabel("Достижения")
        section.setObjectName("section")
        layout.addWidget(section)

        stats_data = {
            "sessions": max(1, int(self.browser.config.get("stats_sessions", 1))),
            "pages": int(self.browser.config.get("stats_pages", 0)),
            "bookmarks": len(load_bookmarks()),
            "shortcuts": len(load_shortcuts()),
            "notes": len(load_notes()),
        }
        achievements = [
            ("🚀", "Первый запуск", "Первый запуск Orbit.", "Запустить Orbit", min(stats_data["sessions"], 1), 1),
            ("🌐", "Исследователь", "Посещайте сайты и открывайте новые страницы.", "Открыть 10 страниц", min(stats_data["pages"], 10), 10),
            ("🔖", "Коллекционер", "Сохраняйте полезные страницы в закладки.", "Добавить 5 закладок", min(stats_data["bookmarks"], 5), 5),
            ("⚡", "Быстрый доступ", "Настройте главную страницу под себя.", "Добавить 3 сайта", min(stats_data["shortcuts"], 3), 3),
            ("📝", "Заметки", "Сохраняйте идеи и полезную информацию.", "Создать 5 заметок", min(stats_data["notes"], 5), 5),
            ("👑", "Создатель Orbit", "Особый статус владельца проекта.", "Права создателя", 1 if role == "founder" else 0, 1),
        ]
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        for i, (icon, title, desc, goal, value, maximum) in enumerate(achievements):
            card = QFrame()
            card.setObjectName("achievementCard")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 15, 16, 15)
            cl.setSpacing(7)
            head = QHBoxLayout()
            ico = QLabel(icon)
            ico.setObjectName("achievementIcon")
            head.addWidget(ico)
            ttl = QLabel(title)
            ttl.setObjectName("achievementTitle")
            head.addWidget(ttl)
            head.addStretch()
            done = value >= maximum
            state = QLabel("Получено" if done else "В процессе")
            state.setObjectName("achievementDone" if done else "achievementProgress")
            head.addWidget(state)
            cl.addLayout(head)
            dd = QLabel(desc)
            dd.setObjectName("achievementDesc")
            dd.setWordWrap(True)
            cl.addWidget(dd)
            goal_label = QLabel(f"Цель: {goal}")
            goal_label.setObjectName("muted")
            goal_label.setWordWrap(True)
            cl.addWidget(goal_label)
            prog = QLabel(f"Прогресс: {value}/{maximum}")
            prog.setObjectName("achievementProgressText")
            cl.addWidget(prog)
            grid.addWidget(card, i // 2, i % 2)
        layout.addLayout(grid)
        layout.addStretch()

    def edit_profile(self):
        dialog = EditProfileDialog(self.browser)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.browser.user = self.browser.user
            self.browser.update_identity_ui()
            self.refresh_avatar()


class EditProfileDialog(QDialog):
    def __init__(self, browser):
        super().__init__(browser); self.browser=browser; self.setWindowTitle("Настройка профиля Orbit"); self.setMinimumWidth(580)
        layout=QVBoxLayout(self); layout.setSpacing(14)
        avatar_row=QHBoxLayout()
        self.avatar_preview=QLabel(); self.avatar_preview.setObjectName("profileAvatar"); self.avatar_preview.setFixedSize(82,82); self.avatar_preview.setAlignment(Qt.AlignmentFlag.AlignCenter); avatar_row.addWidget(self.avatar_preview)
        avatar_col=QVBoxLayout();
        btn=QPushButton("Изменить фотографию"); btn.clicked.connect(self.choose_avatar); avatar_col.addWidget(btn)
        note=QLabel("JPG, PNG или WEBP • хранится локально на этом компьютере"); note.setObjectName("muted"); note.setWordWrap(True); avatar_col.addWidget(note); avatar_row.addLayout(avatar_col); avatar_row.addStretch(); layout.addLayout(avatar_row)
        form=QFormLayout(); self.display=QLineEdit(browser.user.get("display_name") or browser.user.get("username", "")); self.bio=QLineEdit(browser.user.get("bio", "")); self.bio.setPlaceholderText("Коротко расскажите о себе"); self.title=QLineEdit(browser.user.get("title", "Explorer")); self.theme=QComboBox(); self.theme.addItems(THEMES.keys()); self.theme.setCurrentText(browser.user.get("profile_theme", browser.current_theme)); form.addRow("Имя профиля",self.display); form.addRow("О себе",self.bio); form.addRow("Титул",self.title); form.addRow("Тема профиля",self.theme); layout.addLayout(form)
        row=QHBoxLayout(); cancel=QPushButton("Отмена"); save=QPushButton("Сохранить"); save.setProperty("accent",True); row.addWidget(cancel); row.addWidget(save); layout.addLayout(row); cancel.clicked.connect(self.reject); save.clicked.connect(self.save); self.avatar_source=""; self.refresh_preview()

    def refresh_preview(self):
        path=self.avatar_source or self.browser.config.get("avatar_path", "")
        if path and __import__("os").path.exists(path):
            pix=__import__("PySide6.QtGui",fromlist=["QPixmap"]).QPixmap(path); self.avatar_preview.setPixmap(pix.scaled(82,82,Qt.AspectRatioMode.KeepAspectRatioByExpanding,Qt.TransformationMode.SmoothTransformation))
        else:
            name=self.browser.user.get("display_name") or self.browser.user.get("username", "O"); self.avatar_preview.setText(name[0].upper())

    def choose_avatar(self):
        path,_=QFileDialog.getOpenFileName(self,"Выберите фотографию профиля","", "Изображения (*.png *.jpg *.jpeg *.webp)")
        if not path: return
        try:
            AVATAR_FILE.parent.mkdir(parents=True,exist_ok=True); __import__("shutil").copy2(path,AVATAR_FILE); self.avatar_source=str(AVATAR_FILE); self.browser.config["avatar_path"]=str(AVATAR_FILE); from orbit_storage import save_config; save_config(self.browser.config); self.refresh_preview()
        except Exception as exc: QMessageBox.warning(self,"Orbit",f"Не удалось сохранить фотографию:\n{exc}")

    def save(self):
        display_name = self.display.text().strip()
        bio = self.bio.text().strip()
        title = self.title.text().strip()
        profile_theme = self.theme.currentText()
        saved_remote = False
        try:
            response = requests.patch(
                f"{self.browser.API_URL}/api/profile",
                json={"display_name": display_name, "bio": bio, "title": title, "profile_theme": profile_theme},
                headers={"Authorization": f"Bearer {self.browser.token}"},
                timeout=15,
            )
            if response.status_code == 200:
                data = response.json()
                self.browser.user = data.get("user", self.browser.user)
                saved_remote = True
            elif response.status_code != 404:
                QMessageBox.warning(self, "Orbit", "Не удалось сохранить профиль на сервере. Изменения останутся локально до следующей синхронизации.\n\n" + response.text[:300])
        except Exception:
            pass

        self.browser.user["display_name"] = display_name or self.browser.user.get("username", "Orbit")
        self.browser.user["bio"] = bio
        self.browser.user["title"] = title or "Explorer"
        self.browser.user["profile_theme"] = profile_theme
        self.browser.config["avatar_path"] = str(AVATAR_FILE) if AVATAR_FILE.exists() else self.browser.config.get("avatar_path", "")
        from orbit_storage import save_config, save_local_profile
        save_local_profile(self.browser.user)
        save_config(self.browser.config)
        self.browser.current_theme = profile_theme if profile_theme in self.browser.THEMES else self.browser.current_theme
        self.browser.apply_theme()
        self.browser.update_identity_ui()
        self.accept()


class DiagnosticsPage(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 40, 50, 35)
        title = QLabel("Диагностика")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.status = QLabel()
        self.status.setObjectName("muted")
        layout.addWidget(self.status)
        self.details = QListWidget()
        layout.addWidget(self.details, 1)
        run = QPushButton("Проверить всё")
        run.setProperty("accent", True)
        run.clicked.connect(self.run_checks)
        layout.addWidget(run)
        self.run_checks()
        fade_in(self)

    def run_checks(self):
        import platform
        import sys
        self.details.clear()
        checks = []
        checks.append(("Python", sys.version_info >= (3, 13), platform.python_version()))
        try:
            r = requests.get(f"{self.browser.API_URL}/health", timeout=8)
            checks.append(("Orbit API", r.status_code == 200, r.text[:160]))
        except Exception as exc:
            checks.append(("Orbit API", False, str(exc)))
        checks.append(("Session", bool(self.browser.token), "Токен найден" if self.browser.token else "Нет токена"))
        checks.append(("WebEngine", self.browser.web_profile is not None, "QWebEngineProfile"))
        checks.append(("Theme", self.browser.current_theme in THEMES, self.browser.current_theme))
        checks.append(("Site theme", bool(self.browser.config.get("site_theming", True)), "Включена" if self.browser.config.get("site_theming", True) else "Выключена"))
        passed = 0
        for name, ok, info in checks:
            if ok:
                passed += 1
            self.details.addItem(f"[{ 'OK' if ok else 'ERROR' }] {name}\n{info}")
        self.status.setText(f"Пройдено {passed}/{len(checks)} проверок.")


class SettingsPage(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.cards = []
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(48, 34, 48, 28)
        self.layout.setSpacing(12)
        self.build()
        fade_in(self)

    def add_card(self, title, description, control):
        card = QFrame()
        card.setObjectName("settingCard")
        row = QHBoxLayout(card)
        row.setContentsMargins(18, 14, 14, 14)
        texts = QVBoxLayout()
        name = QLabel(title)
        name.setObjectName("settingTitle")
        desc = QLabel(description)
        desc.setObjectName("settingDescription")
        desc.setWordWrap(True)
        texts.addWidget(name)
        texts.addWidget(desc)
        row.addLayout(texts, 1)
        row.addWidget(control)
        self.layout.addWidget(card)
        self.cards.append((name, desc))

    def build(self):
        self.title = QLabel("Настройки")
        self.title.setObjectName("pageTitle")
        self.layout.addWidget(self.title)
        self.subtitle = QLabel("Все важные параметры Orbit собраны здесь. Справа показано, что именно изменит каждая настройка.")
        self.subtitle.setObjectName("muted")
        self.subtitle.setWordWrap(True)
        self.layout.addWidget(self.subtitle)

        language = QComboBox()
        language.addItem("Русский", "ru")
        language.addItem("English", "en")
        language.setCurrentIndex(language.findData(self.browser.config.get("language", "ru")))
        language.currentIndexChanged.connect(self.change_language)
        self.add_card("Язык интерфейса", "Меняет язык основных элементов Orbit: меню, главной страницы и подсказок.", language)

        theme = QComboBox()
        theme.addItems(THEMES.keys())
        theme.setCurrentText(self.browser.current_theme)
        theme.currentTextChanged.connect(self.browser.change_theme)
        self.add_card("Тема Orbit", "Меняет фон, акцентный цвет, панели и общий внешний вид браузера.", theme)

        engine = QComboBox()
        for label, data in [("Google", "google"), ("Bing", "bing"), ("DuckDuckGo", "duckduckgo"), ("Orbit", "orbit")]:
            engine.addItem(label, data)
        idx = engine.findData(self.browser.config.get("search_engine", "google"))
        engine.setCurrentIndex(idx if idx >= 0 else 0)
        engine.currentIndexChanged.connect(self.save_engine)
        self.add_card("Поисковая система", "Определяет, куда Orbit отправляет запросы из адресной строки и главного поиска.", engine)
        self.engine_control = engine

        auto = QPushButton("Включено" if self.browser.config.get("auto_update", True) else "Выключено")
        auto.clicked.connect(lambda: self.toggle_bool("auto_update", auto))
        self.add_card("Автоматические обновления", "Проверяет новые версии Orbit и предлагает скачать официальный установщик.", auto)

        site = QPushButton("Включено" if self.browser.config.get("site_theming", True) else "Выключено")
        site.clicked.connect(lambda: self.toggle_bool("site_theming", site))
        self.add_card("Оформление сайтов Orbit", "Пытается применять тёмную палитру Orbit к открытым сайтам. Отключите, если какой-то сайт отображается неправильно.", site)

        anim = QPushButton("Включено" if self.browser.config.get("animations", True) else "Выключено")
        anim.clicked.connect(lambda: self.toggle_bool("animations", anim))
        self.add_card("Плавные анимации", "Включает мягкие появления и переходы интерфейса. Отключение может сделать интерфейс быстрее на слабом ПК.", anim)

        self.layout.addStretch()

    def save_engine(self, index):
        self.browser.config["search_engine"] = self.engine_control.itemData(index)
        from orbit_storage import save_config
        save_config(self.browser.config)
        if hasattr(self.browser, "home"):
            self.browser.home.engine_hint.setText({"google":"Google","bing":"Bing","duckduckgo":"DuckDuckGo","orbit":"Orbit"}.get(self.browser.config["search_engine"], "Google"))

    def toggle_bool(self, key, button):
        enabled = not self.browser.config.get(key, True)
        self.browser.config[key] = enabled
        from orbit_storage import save_config
        save_config(self.browser.config)
        button.setText("Включено" if enabled else "Выключено")
        if key == "site_theming":
            self.browser.apply_theme()

    def change_language(self, index):
        self.browser.config["language"] = self.sender().itemData(index)
        from orbit_storage import save_config
        save_config(self.browser.config)
        self.browser.apply_language()
        self.title.setText("Настройки" if self.browser.config["language"] == "ru" else "Settings")
        self.subtitle.setText("Все важные параметры Orbit собраны здесь. Справа показано, что именно изменит каждая настройка." if self.browser.config["language"] == "ru" else "All important Orbit settings are here. Each option explains what it changes.")

