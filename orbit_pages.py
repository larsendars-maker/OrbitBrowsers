from urllib.parse import quote_plus, unquote_plus
import re
import os
import sys
import subprocess

import requests
from PySide6.QtCore import Qt, Signal, QObject, QThread, QTimer, QUrl
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QDialog,
    QFormLayout,
    QFrame,
    QInputDialog,
    QMenu,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QScrollArea,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QMenu,
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
    load_history,
    load_downloads,
    save_downloads, update_download, remove_download,
)
from orbit_ui import THEMES, fade_in, tr




class LoginPage(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser=browser
        layout=QVBoxLayout(self)
        layout.setContentsMargins(80,70,80,70)
        title=QLabel("Orbit Account")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        info=QLabel("Войдите или создайте аккаунт. Окно регистрации открывается внутри Orbit, без внешнего браузера.")
        info.setWordWrap(True); info.setObjectName("muted"); layout.addWidget(info)
        self.email=QLineEdit(); self.email.setPlaceholderText("Email"); layout.addWidget(self.email)
        self.password=QLineEdit(); self.password.setPlaceholderText("Пароль"); self.password.setEchoMode(QLineEdit.EchoMode.Password); layout.addWidget(self.password)
        self.username=QLineEdit(); self.username.setPlaceholderText("Имя пользователя — только для регистрации"); layout.addWidget(self.username)
        row=QHBoxLayout()
        login=QPushButton("Войти"); login.setProperty("accent",True); register=QPushButton("Создать аккаунт")
        row.addWidget(login); row.addWidget(register); layout.addLayout(row)
        self.status=QLabel(""); self.status.setWordWrap(True); self.status.setObjectName("muted"); layout.addWidget(self.status); layout.addStretch()
        login.clicked.connect(self.login); register.clicked.connect(self.register)
        fade_in(self)

    def login(self):
        email=self.email.text().strip(); password=self.password.text()
        if not email or not password: self.status.setText("Введите email и пароль."); return
        try:
            r=requests.post(f"{self.browser.API_URL}/api/auth/login",json={"email":email,"password":password},timeout=12)
            if r.status_code>=400: self.status.setText(r.text[:300]); return
            data=r.json(); self.browser.set_session(data.get("token"),data.get("user")); self.browser.show_home_screen()
        except Exception as exc: self.status.setText(f"Ошибка соединения: {exc}")

    def register(self):
        username=self.username.text().strip(); email=self.email.text().strip(); password=self.password.text()
        if not username or not email or len(password)<8: self.status.setText("Для регистрации нужны имя, email и пароль минимум 8 символов."); return
        try:
            r=requests.post(f"{self.browser.API_URL}/api/auth/register",json={"username":username,"email":email,"password":password},timeout=12)
            if r.status_code>=400: self.status.setText(r.text[:300]); return
            data=r.json(); self.browser.set_session(data.get("token"),data.get("user")); self.browser.show_home_screen()
        except Exception as exc: self.status.setText(f"Ошибка соединения: {exc}")

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


class ConnectionDialog(QDialog):
    def __init__(self, browser):
        super().__init__(browser)
        self.browser = browser
        self.setWindowTitle("Orbit Connect")
        self.setMinimumWidth(560)
        layout = QVBoxLayout(self)
        title = QLabel("Orbit Connect")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        info = QLabel("Укажите свой HTTP/HTTPS или SOCKS5 прокси. Orbit применит его ко всему Chromium после перезапуска.")
        info.setWordWrap(True)
        info.setObjectName("muted")
        layout.addWidget(info)
        self.proxy = QLineEdit(browser.config.get("proxy_url", ""))
        self.proxy.setPlaceholderText("http://127.0.0.1:8080 или socks5://127.0.0.1:1080")
        layout.addWidget(self.proxy)
        self.status = QLabel("")
        self.status.setObjectName("muted")
        layout.addWidget(self.status)
        row = QHBoxLayout()
        clear = QPushButton("Отключить")
        save = QPushButton("Сохранить")
        save.setProperty("accent", True)
        row.addWidget(clear)
        row.addStretch()
        row.addWidget(save)
        layout.addLayout(row)
        clear.clicked.connect(lambda: self.proxy.setText(""))
        save.clicked.connect(self.save)

    def save(self):
        value = self.proxy.text().strip()
        if value and not (value.startswith("http://") or value.startswith("https://") or value.startswith("socks5://")):
            QMessageBox.warning(self, "Orbit", "Используйте http://, https:// или socks5://")
            return
        self.browser.config["proxy_url"] = value
        from orbit_storage import save_config
        save_config(self.browser.config)
        self.status.setText("Сохранено. Перезапустите Orbit, чтобы применить сетевой прокси.")
        self.accept()


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
        search_shell.setMaximumWidth(840)
        search_shell.setMinimumWidth(720)
        search_shell.setMinimumHeight(54)
        search_row = QHBoxLayout(search_shell)
        search_row.setContentsMargins(12, 6, 10, 6)
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
        }.get(self.browser.config.get("search_engine", "orbit"), "Orbit")
        self.engine_hint = QPushButton(engine_name)
        self.engine_hint.setObjectName("searchUtility")
        self.engine_hint.setToolTip("Выбрать поисковую систему / Choose search engine")
        self.engine_hint.clicked.connect(self.browser.open_settings)
        search_row.addWidget(self.engine_hint)

        go = QPushButton("→")
        go.setObjectName("searchButton")
        go.setFixedSize(46, 46)
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
        connect = QPushButton("◌  Сеть")
        connect.setObjectName("addShortcut")
        connect.setToolTip("Настроить прокси для подключений, если это разрешено вашей сетью")
        connect.clicked.connect(lambda: ConnectionDialog(self.browser).exec())
        quick_row.addWidget(connect)
        self.connection_button = connect

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
            name = {"google":"Google", "bing":"Bing", "duckduckgo":"DuckDuckGo", "orbit":"Orbit"}.get(self.browser.config.get("search_engine", "orbit"), "Orbit")
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
    def __init__(self, browser, query="", force_orbit=False):
        super().__init__()
        self.browser = browser
        self.query = query
        self.force_orbit = force_orbit
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

        # Orbit Search — внутренняя страница Orbit. Внешний провайдер
        # используется только после выбора пользователем и открывается
        # в текущей вкладке, без отдельного окна.
        if self.force_orbit or self.browser.config.get("search_engine", "orbit") == "orbit":
            self.browser.show_search_results(query)
            return
        self.browser.open_url(self.browser.search_url(query))

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
        layout.setSpacing(12)
        header = QHBoxLayout()
        title = QLabel("История")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()
        clear = QPushButton("Очистить историю")
        clear.setObjectName("dangerButton")
        clear.clicked.connect(self.clear_history)
        header.addWidget(clear)
        refresh = QPushButton("↻ Обновить")
        refresh.clicked.connect(self.refresh)
        header.addWidget(refresh)
        layout.addLayout(header)
        self.list = QListWidget()
        self.list.setSpacing(8)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list.setAlternatingRowColors(False)
        self.list.itemDoubleClicked.connect(self.open_item)
        layout.addWidget(self.list, 1)
        actions = QHBoxLayout()
        open_btn = QPushButton("Открыть")
        remove_btn = QPushButton("Удалить")
        open_btn.clicked.connect(self.open_selected)
        remove_btn.clicked.connect(self.remove_selected)
        actions.addWidget(open_btn); actions.addWidget(remove_btn); actions.addStretch()
        layout.addLayout(actions)
        self.refresh()
        fade_in(self)

    def refresh(self):
        self.list.clear()
        items = list(reversed(load_history()))
        for entry in items:
            title = entry.get("title") or entry.get("url") or "Без названия"
            url = entry.get("url", "")
            import datetime
            ts = entry.get("timestamp") or 0
            when = datetime.datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M") if ts else ""
            text = f"{title}\n{url}\n{when}"
            row = QListWidgetItem(text)
            row.setData(Qt.ItemDataRole.UserRole, url)
            self.list.addItem(row)
        if not items:
            self.list.addItem("История пока пуста")

    def selected_url(self):
        item = self.list.currentItem()
        if not item:
            return ""
        return item.data(Qt.ItemDataRole.UserRole) or ""

    def open_selected(self):
        url = self.selected_url()
        if url: self.browser.open_url(url)

    def open_item(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url: self.browser.open_url(url)

    def remove_selected(self):
        urls = []
        for item in self.list.selectedItems():
            value = item.data(Qt.ItemDataRole.UserRole)
            if value:
                urls.append(value)
        if not urls:
            return
        items = [x for x in load_history() if x.get("url") not in set(urls)]
        from orbit_storage import save_history
        save_history(items)
        self.refresh()

    def clear_history(self):
        from orbit_storage import save_history
        save_history([])
        self.refresh()


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
        self.browser = browser
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 40, 50, 35)
        layout.setSpacing(12)
        header = QHBoxLayout()
        title = QLabel("Загрузки")
        title.setObjectName("pageTitle")
        header.addWidget(title); header.addStretch()
        refresh = QPushButton("↻ Обновить")
        refresh.clicked.connect(self.refresh)
        header.addWidget(refresh)
        layout.addLayout(header)
        self.list = QListWidget()
        self.list.setSpacing(8)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list.setAlternatingRowColors(False)
        layout.addWidget(self.list, 1)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.show_file_menu)
        actions = QHBoxLayout()
        for text, slot in [
            ("Открыть", self.open_selected),
            ("Открыть папку", self.open_folder),
            ("Переименовать", self.rename_selected),
            ("Удалить из списка", self.remove_selected),
            ("Удалить файл", self.delete_file_and_record),
            ("VirusTotal", self.virustotal_selected),
        ]:
            b = QPushButton(text); b.clicked.connect(slot); actions.addWidget(b)
        layout.addLayout(actions)
        self.list.itemDoubleClicked.connect(self.open_item)
        self.refresh(); fade_in(self)

    def refresh(self):
        self.list.clear()
        items = load_downloads()
        if not items:
            self.list.addItem("Загрузок пока нет")
            return
        for item in items:
            path = item.get("path", "")
            state = item.get("state", "completed")
            title = item.get("filename") or os.path.basename(path) or "Файл"
            row = QListWidgetItem(f"{title}  ·  {state}\n{path}")
            row.setData(Qt.ItemDataRole.UserRole, path)
            self.list.addItem(row)

    def selected_paths(self):
        paths = []
        for item in self.list.selectedItems():
            value = item.data(Qt.ItemDataRole.UserRole)
            if value:
                paths.append(value)
        return paths

    def selected_path(self):
        paths = self.selected_paths()
        return paths[0] if paths else ""

    def open_item(self, item):
        self.open_path(item.data(Qt.ItemDataRole.UserRole) or "")

    def show_file_menu(self, position):
        item = self.list.itemAt(position)
        if item is None:
            return
        self.list.setCurrentItem(item)
        path = item.data(Qt.ItemDataRole.UserRole) or ""
        menu = QMenu(self)

        act_open = menu.addAction("Открыть")
        act_folder = menu.addAction("Открыть папку")
        act_rename = menu.addAction("Переименовать")
        menu.addSeparator()
        act_vt = menu.addAction("Проверить в VirusTotal")
        menu.addSeparator()
        act_delete_record = menu.addAction("Удалить из списка")
        act_delete_file = menu.addAction("Удалить файл")

        chosen = menu.exec(self.list.viewport().mapToGlobal(position))
        if chosen is act_open:
            self.open_selected()
        elif chosen is act_folder:
            self.open_folder()
        elif chosen is act_rename:
            self.rename_selected()
        elif chosen is act_vt:
            self.virustotal_selected()
        elif chosen is act_delete_record:
            self.remove_selected()
        elif chosen is act_delete_file:
            self.delete_file_and_record()

    def delete_file_and_record(self):
        paths = self.selected_paths()
        if not paths:
            return
        errors = []
        for path in paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                remove_download(path)
            except Exception as exc:
                errors.append(f"{os.path.basename(path)}: {exc}")
        self.refresh()
        if errors:
            QMessageBox.warning(self, "Orbit", "Не удалось удалить некоторые файлы:\n" + "\n".join(errors))

    def open_path(self, path):
        if not path or not os.path.exists(path): return
        if sys.platform == "win32": os.startfile(path)
        else: subprocess.Popen(["xdg-open", path])

    def open_selected(self): self.open_path(self.selected_path())

    def open_folder(self):
        path = self.selected_path()
        if not path: return
        folder = os.path.dirname(path)
        if sys.platform == "win32": subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
        elif os.path.isdir(folder): subprocess.Popen(["xdg-open", folder])

    def rename_selected(self):
        path = self.selected_path()
        if not path or not os.path.exists(path): return
        old_name = os.path.basename(path)
        dialog = QDialog(self); dialog.setWindowTitle("Переименовать файл"); form=QFormLayout(dialog)
        field=QLineEdit(old_name); form.addRow("Новое имя", field); row=QHBoxLayout(); ok=QPushButton("Сохранить"); cancel=QPushButton("Отмена"); row.addWidget(cancel); row.addWidget(ok); form.addRow(row)
        cancel.clicked.connect(dialog.reject); ok.clicked.connect(dialog.accept)
        if dialog.exec() != QDialog.DialogCode.Accepted: return
        new_name = os.path.basename(field.text().strip())
        if not new_name: return
        new_path = os.path.join(os.path.dirname(path), new_name)
        try:
            os.rename(path, new_path)
            update_download(path, filename=new_name, path=new_path)
            self.refresh()
        except Exception as exc:
            QMessageBox.warning(self, "Orbit", f"Не удалось переименовать файл:\n{exc}")

    def remove_selected(self):
        paths = self.selected_paths()
        if not paths:
            return
        for path in paths:
            remove_download(path)
        self.refresh()

    def virustotal_selected(self):
        path = self.selected_path()
        if not path: return
        if os.path.exists(path):
            QMessageBox.information(self, "VirusTotal", "Откроется VirusTotal. Для проверки выберите этот файл в загрузчике VirusTotal.")
        self.browser.open_url("https://www.virustotal.com/gui/home/upload")


ACHIEVEMENTS = [
    {"key": "first_launch", "icon": "✦", "title": "Первый шаг", "desc": "Запустите Orbit хотя бы один раз.", "goal": "1 запуск", "stat": "sessions", "maximum": 1, "reward": "Новичок"},
    {"key": "explorer", "icon": "◎", "title": "Исследователь", "desc": "Открывайте новые страницы и изучайте интернет.", "goal": "10 страниц", "stat": "pages", "maximum": 10, "reward": "Исследователь"},
    {"key": "collector", "icon": "☆", "title": "Коллекционер", "desc": "Соберите полезные страницы в закладках.", "goal": "5 закладок", "stat": "bookmarks", "maximum": 5, "reward": "Коллекционер"},
    {"key": "navigator", "icon": "⌁", "title": "Навигатор", "desc": "Настройте быстрый доступ под себя.", "goal": "3 сайта", "stat": "shortcuts", "maximum": 3, "reward": "Навигатор"},
    {"key": "notes", "icon": "✎", "title": "Архивариус", "desc": "Сохраняйте полезные идеи и записи.", "goal": "5 заметок", "stat": "notes", "maximum": 5, "reward": "Архивариус"},
    {"key": "founder", "icon": "◆", "title": "Создатель Orbit", "desc": "Особый титул владельца проекта Orbit.", "goal": "Статус создателя", "stat": "founder", "maximum": 1, "reward": "Создатель Orbit"},
]

def _profile_stats(browser, role):
    return {
        "sessions": max(1, int(browser.config.get("stats_sessions", 1))),
        "pages": int(browser.config.get("stats_pages", 0)),
        "bookmarks": len(load_bookmarks()),
        "shortcuts": len(load_shortcuts()),
        "notes": len(load_notes()),
        "founder": 1 if (browser.user.get("username", "").lower() == "larsenda" or browser.user.get("title") == "Создатель Orbit") else 0,
    }

def sync_unlocked_titles(browser, stats):
    unlocked = set(browser.user.get("unlocked_titles") or [])
    title_map = {
        "Новичок":"newcomer", "Исследователь":"explorer", "Коллекционер":"collector",
        "Навигатор":"navigator", "Архивариус":"archivist", "Создатель Orbit":"creator",
        "Помощник":"helper", "Администратор":"admin", "Explorer":"explorer"
    }
    for item in ACHIEVEMENTS:
        value = min(stats.get(item["stat"], 0), item["maximum"])
        if value >= item["maximum"]:
            unlocked.add(item["reward"])
            try:
                requests.post(
                    f"{browser.API_URL}/api/profile/achievements/claim",
                    json={"achievement_key": item["key"]},
                    headers={"Authorization": f"Bearer {browser.token}"},
                    timeout=4,
                )
            except Exception:
                pass
    unlocked.add("Explorer")
    role = browser.user.get("role", "user").lower()
    if role == "helper": unlocked.add("Помощник")
    if role == "admin": unlocked.add("Администратор")
    browser.user["unlocked_titles"] = sorted(unlocked)
    current = browser.user.get("equipped_title") or browser.user.get("title") or "Explorer"
    if current not in unlocked:
        current = "Explorer"
    browser.user["equipped_title"] = current
    browser.user["title"] = current
    from orbit_storage import save_local_profile
    save_local_profile(browser.user)
    return unlocked


class ProfilePage(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.sync_titles_from_server()
        self.build()
        fade_in(self, 240)

    def sync_titles_from_server(self):
        try:
            response = requests.get(
                f"{self.browser.API_URL}/api/profile/titles",
                headers={"Authorization": f"Bearer {self.browser.token}"},
                timeout=8,
            )
            if response.status_code != 200:
                return
            data = response.json()
            unlocked = [t.get("name_ru") for t in data.get("titles", []) if t.get("unlocked")]
            if unlocked:
                self.browser.user["unlocked_titles"] = sorted(set(unlocked))
            equipped = data.get("equipped")
            if equipped:
                self.browser.user["equipped_title"] = equipped
                self.browser.user["title"] = equipped
            from orbit_storage import save_local_profile
            save_local_profile(self.browser.user)
        except Exception:
            pass

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
        sync_unlocked_titles(self.browser, _profile_stats(self.browser, role))
        role_label = QLabel(self.browser.user.get("equipped_title") or "Explorer")
        role_label.setObjectName("founderBadge" if (self.browser.user.get("equipped_title") == "Создатель Orbit") else "muted")
        self.current_title_label = role_label
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
        for value, label in [(str(level), "Уровень"), (str(xp), "XP"), ({"admin":"Админ","helper":"Помощник"}.get(role, "Пользователь"), "Статус")]:
            card = QFrame()
            card.setObjectName("profileStat")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(18, 16, 18, 16)
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

        role = user.get("role", "user")
        stats_data = _profile_stats(self.browser, role)
        sync_unlocked_titles(self.browser, stats_data)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        grid = QGridLayout(scroll_content)
        grid.setContentsMargins(2, 2, 12, 8)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)
        for i, item in enumerate(ACHIEVEMENTS):
            value = min(stats_data.get(item["stat"], 0), item["maximum"])
            done = value >= item["maximum"]
            card = QFrame()
            card.setObjectName("achievementCard")
            card.setProperty("done", "true" if done else "false")
            card.setMinimumHeight(172)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(18, 16, 18, 16)
            cl.setSpacing(8)
            head = QHBoxLayout()
            ico = QLabel(item["icon"])
            ico.setObjectName("achievementIcon")
            head.addWidget(ico)
            ttl = QLabel(item["title"])
            ttl.setObjectName("achievementTitle")
            ttl.setWordWrap(True)
            ttl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            head.addWidget(ttl, 1)
            head.addStretch()
            state = QLabel("Получено" if done else "В процессе")
            state.setObjectName("achievementDone" if done else "achievementProgress")
            state.setAlignment(Qt.AlignmentFlag.AlignCenter)
            state.setMinimumWidth(96)
            head.addWidget(state, 0, Qt.AlignmentFlag.AlignTop)
            cl.addLayout(head)
            dd = QLabel(item["desc"])
            dd.setObjectName("achievementDesc")
            dd.setWordWrap(True)
            dd.setMinimumHeight(30)
            cl.addWidget(dd)
            reward = QLabel(f"Награда: титул «{item['reward']}»")
            reward.setObjectName("achievementReward")
            reward.setWordWrap(True)
            cl.addWidget(reward)
            prog = QLabel(f"Прогресс: {value}/{item['maximum']}")
            prog.setObjectName("achievementProgressText")
            cl.addWidget(prog)
            if done:
                card.setToolTip(f"Нажмите, чтобы надеть титул «{item['reward']}»")
                card.mousePressEvent = lambda _e, reward=item["reward"]: self.equip_title(reward)
            else:
                card.setToolTip(f"Выполните: {item['goal']}")
            grid.addWidget(card, i // 2, i % 2)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

    def equip_title(self, title):
        unlocked = set(self.browser.user.get("unlocked_titles") or [])
        if title not in unlocked:
            return
        self.browser.user["equipped_title"] = title
        self.browser.user["title"] = title
        from orbit_storage import save_local_profile
        save_local_profile(self.browser.user)
        try:
            requests.post(
                f"{self.browser.API_URL}/api/profile/title",
                json={"title_key": {"Новичок":"newcomer","Исследователь":"explorer","Коллекционер":"collector","Навигатор":"navigator","Архивариус":"archivist","Создатель Orbit":"creator","Помощник":"helper","Администратор":"admin","Explorer":"explorer"}.get(title, "")},
                headers={"Authorization": f"Bearer {self.browser.token}"},
                timeout=8,
            )
        except Exception:
            pass
        if hasattr(self, "current_title_label"):
            self.current_title_label.setText(title)
            self.current_title_label.setObjectName("founderBadge" if title == "Создатель Orbit" else "muted")
            self.current_title_label.style().unpolish(self.current_title_label)
            self.current_title_label.style().polish(self.current_title_label)
        self.browser.update_identity_ui()
        try:
            self.browser.identityChanged.emit()
        except Exception:
            pass

    def edit_profile(self):
        dialog = EditProfileDialog(self.browser)
        if dialog.exec() == QDialog.DialogCode.Accepted:
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
        form=QFormLayout(); self.display=QLineEdit(browser.user.get("display_name") or browser.user.get("username", "")); self.bio=QLineEdit(browser.user.get("bio", "")); self.bio.setPlaceholderText("Коротко расскажите о себе"); self.title_info=QComboBox(); self.title_info.setToolTip("Можно выбрать только уже полученный титул"); unlocked = browser.user.get("unlocked_titles") or [browser.user.get("equipped_title") or browser.user.get("title", "Explorer")]; current_title=browser.user.get("equipped_title") or browser.user.get("title", "Explorer");
        for title_item in unlocked:
            if title_item and self.title_info.findText(title_item) < 0: self.title_info.addItem(title_item);
        idx=self.title_info.findText(current_title);
        if idx >= 0: self.title_info.setCurrentIndex(idx);
        self.theme=QComboBox(); self.theme.addItems(THEMES.keys()); self.theme.setCurrentText(browser.user.get("profile_theme", browser.current_theme)); form.addRow("Имя профиля",self.display); form.addRow("О себе",self.bio); form.addRow("Титул",self.title_info); form.addRow("Тема профиля",self.theme); layout.addLayout(form)
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
        title = self.title_info.currentText().strip() or "Explorer"
        profile_theme = self.theme.currentText()
        try:
            response = requests.patch(
                f"{self.browser.API_URL}/api/profile",
                json={"display_name": display_name, "bio": bio, "profile_theme": profile_theme},
                headers={"Authorization": f"Bearer {self.browser.token}"},
                timeout=15,
            )
            if response.status_code == 200:
                self.browser.user = response.json().get("user", self.browser.user)
            elif response.status_code != 404:
                QMessageBox.warning(self, "Orbit", "Не удалось сохранить профиль на сервере. Изменения останутся локально.\n\n" + response.text[:300])
            title_keys={"Новичок":"newcomer","Исследователь":"explorer","Коллекционер":"collector","Навигатор":"navigator","Архивариус":"archivist","Создатель Orbit":"creator","Помощник":"helper","Администратор":"admin","Explorer":"explorer"}
            title_key=title_keys.get(title)
            if title_key:
                title_response = requests.post(
                    f"{self.browser.API_URL}/api/profile/title",
                    json={"title_key": title_key},
                    headers={"Authorization": f"Bearer {self.browser.token}"},
                    timeout=8,
                )
                if title_response.status_code == 200:
                    payload = title_response.json().get("user")
                    if payload:
                        self.browser.user.update(payload)
        except Exception:
            pass

        self.browser.user["display_name"] = display_name or self.browser.user.get("username", "Orbit")
        self.browser.user["bio"] = bio
        self.browser.user["title"] = title or "Explorer"
        self.browser.user["equipped_title"] = title or "Explorer"
        self.browser.user["profile_theme"] = profile_theme
        self.browser.config["avatar_path"] = str(AVATAR_FILE) if AVATAR_FILE.exists() else self.browser.config.get("avatar_path", "")
        from orbit_storage import save_config, save_local_profile
        save_local_profile(self.browser.user)
        save_config(self.browser.config)
        self.browser.current_theme = profile_theme if profile_theme in self.browser.THEMES else self.browser.current_theme
        self.browser.apply_theme()
        self.browser.update_identity_ui()
        try:
            self.browser.identityChanged.emit()
        except Exception:
            pass
        self.accept()


class GeminiWorker(QObject):
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, browser, model, message, images, previous_interaction_id):
        super().__init__()
        self.browser = browser
        self.model = model
        self.message = message
        self.images = images
        self.previous_interaction_id = previous_interaction_id

    def run(self):
        try:
            import base64
            payload = {
                "model": self.model,
                "message": self.message,
                "previous_interaction_id": self.previous_interaction_id,
                "images": [],
            }
            for image_path, mime_type in self.images:
                with open(image_path, "rb") as f:
                    raw = f.read()
                if len(raw) > 12 * 1024 * 1024:
                    raise ValueError("Изображение слишком большое (максимум 12 МБ).")
                payload["images"].append({"mime_type": mime_type, "data": base64.b64encode(raw).decode("ascii")})
            response = requests.post(
                f"{self.browser.API_URL}/api/ai/chat",
                json=payload,
                headers={"Authorization": f"Bearer {self.browser.token}"},
                timeout=180,
            )
            if response.status_code >= 400:
                try:
                    detail = response.json().get("detail", response.text)
                except Exception:
                    detail = response.text
                raise RuntimeError(str(detail))
            self.finished.emit(response.json())
        except Exception as exc:
            self.failed.emit(str(exc))


class GeminiPage(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.interaction_id = None
        self.attachments = []
        self.thread = None
        self.worker = None
        self.models = []
        self.language = self.browser.config.get("language", "ru")
        self.build()
        self.load_models()
        fade_in(self, 220)

    def tr(self, ru, en):
        return ru if self.browser.config.get("language", "ru") == "ru" else en

    def build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(12)

        header = QFrame()
        header.setObjectName("aiHeader")
        h = QHBoxLayout(header)
        h.setContentsMargins(18, 14, 18, 14)
        title_box = QVBoxLayout()
        title = QLabel("Orbit AI")
        title.setObjectName("aiTitle")
        subtitle = QLabel(self.tr("Gemini внутри Orbit — задавайте вопросы, прикладывайте фото и меняйте модель.", "Gemini inside Orbit — ask questions, attach photos and switch models."))
        subtitle.setObjectName("aiSubtitle")
        subtitle.setWordWrap(True)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        h.addLayout(title_box, 1)

        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(250)
        self.model_combo.setToolTip(self.tr("Выберите модель Gemini", "Choose a Gemini model"))
        h.addWidget(self.model_combo)
        new_chat = QPushButton(self.tr("Новый чат", "New chat"))
        new_chat.setProperty("accent", False)
        new_chat.clicked.connect(self.new_chat)
        h.addWidget(new_chat)
        layout.addWidget(header)

        quick = QHBoxLayout()
        for label, prompt in [
            (self.tr("Разобрать фото", "Analyze photo"), "Разбери прикреплённое фото подробно: что на нём, важный текст и что означает изображение."),
            (self.tr("Перевести", "Translate"), "Переведи текст с прикреплённого фото. Сохрани смысл и укажи перевод по строкам."),
            (self.tr("Решить задачу", "Solve task"), "Реши задачу с фото пошагово и объясни ход решения."),
            (self.tr("Объяснить", "Explain"), "Объясни содержимое прикреплённого фото простыми словами.")
        ]:
            btn = QPushButton(label)
            btn.setObjectName("aiQuickAction")
            btn.clicked.connect(lambda _, p=prompt: self.set_quick_prompt(p))
            quick.addWidget(btn)
        quick.addStretch()
        layout.addLayout(quick)

        self.chat = QListWidget()
        self.chat.setObjectName("aiChat")
        self.chat.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.chat.setSpacing(10)
        self.chat.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.chat, 1)

        attach_row = QHBoxLayout()
        attach = QPushButton("＋ " + self.tr("Фото", "Photo"))
        attach.setObjectName("aiAttachment")
        attach.clicked.connect(self.choose_images)
        attach_row.addWidget(attach)
        self.attachment_label = QLabel(self.tr("Нет вложений", "No attachments"))
        self.attachment_label.setObjectName("aiAttachmentLabel")
        attach_row.addWidget(self.attachment_label, 1)
        layout.addLayout(attach_row)

        composer = QFrame()
        composer.setObjectName("aiComposer")
        c = QHBoxLayout(composer)
        c.setContentsMargins(10, 10, 10, 10)
        self.input = QTextEdit()
        self.input.setObjectName("aiInput")
        self.input.setFixedHeight(74)
        self.input.setPlaceholderText(self.tr("Напишите вопрос…", "Ask Gemini anything…"))
        c.addWidget(self.input, 1)
        send = QPushButton("↑")
        send.setObjectName("aiSend")
        send.setProperty("accent", True)
        send.setFixedSize(54, 54)
        send.clicked.connect(self.send_message)
        c.addWidget(send)
        layout.addWidget(composer)

        self.status = QLabel(self.tr("Готово", "Ready"))
        self.status.setObjectName("aiStatus")
        layout.addWidget(self.status)

    def load_models(self):
        try:
            response = requests.get(
                f"{self.browser.API_URL}/api/ai/models",
                headers={"Authorization": f"Bearer {self.browser.token}"},
                timeout=15,
            )
            if response.status_code != 200:
                self.status.setText(self.tr("Не удалось загрузить список моделей.", "Could not load model list."))
                return
            data = response.json()
            self.models = data.get("models") or []
            self.model_combo.clear()
            preferred = self.browser.config.get("gemini_model", "gemini-3.8-flash")
            preferred_index = 0
            for index, model in enumerate(self.models):
                self.model_combo.addItem(model.get("name", model.get("id")), model.get("id"))
                self.model_combo.setItemData(index, model.get("description", ""), Qt.ItemDataRole.ToolTipRole)
                if model.get("id") == preferred:
                    preferred_index = index
            if self.models:
                self.model_combo.setCurrentIndex(preferred_index)
                self.browser.config["gemini_model"] = self.model_combo.currentData()
                from orbit_storage import save_config
                save_config(self.browser.config)
                if data.get("configured"):
                    self.status.setText(self.tr("Gemini готов. Можно писать или прикрепить фото.", "Gemini is ready. Send a message or attach a photo."))
                else:
                    self.status.setText(self.tr("Добавьте GEMINI_API_KEY в переменные окружения сервера, чтобы включить чат.", "Add GEMINI_API_KEY to the server environment to enable chat."))
        except Exception as exc:
            self.status.setText(self.tr("Сервер Orbit AI недоступен.", "Orbit AI server is unavailable.") + f"  {exc}")

    def add_message(self, role, text, images=None):
        wrapper = QFrame()
        wrapper.setObjectName("aiMessageUser" if role == "user" else "aiMessageAssistant")
        box = QVBoxLayout(wrapper)
        box.setContentsMargins(14, 12, 14, 12)
        who = QLabel("Вы" if role == "user" else "Gemini")
        who.setObjectName("aiMessageAuthor")
        box.addWidget(who)
        if images:
            chips = QHBoxLayout()
            for path, _ in images:
                label = QLabel(os.path.basename(path))
                label.setObjectName("aiImageChip")
                chips.addWidget(label)
            chips.addStretch()
            box.addLayout(chips)
        body = QLabel(text)
        body.setObjectName("aiMessageText")
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        box.addWidget(body)
        item = QListWidgetItem()
        item.setSizeHint(wrapper.sizeHint())
        self.chat.addItem(item)
        self.chat.setItemWidget(item, wrapper)
        self.chat.scrollToBottom()

    def set_quick_prompt(self, prompt):
        self.input.setPlainText(prompt)
        self.input.setFocus()

    def choose_images(self):
        paths, _ = QFileDialog.getOpenFileNames(self, self.tr("Выбрать фото", "Choose images"), "", "Изображения (*.png *.jpg *.jpeg *.webp)")
        if not paths:
            return
        self.attachments = []
        for path in paths[:4]:
            lower = path.lower()
            mime = "image/png" if lower.endswith(".png") else "image/webp" if lower.endswith(".webp") else "image/jpeg"
            self.attachments.append((path, mime))
        self.attachment_label.setText(", ".join(os.path.basename(p) for p, _ in self.attachments))

    def new_chat(self):
        self.interaction_id = None
        self.attachments = []
        self.attachment_label.setText(self.tr("Нет вложений", "No attachments"))
        self.chat.clear()
        self.status.setText(self.tr("Новый чат готов.", "New chat is ready."))

    def send_message(self):
        if self.thread is not None:
            return
        message = self.input.toPlainText().strip()
        images = list(self.attachments)
        if not message and not images:
            return
        model = self.model_combo.currentData() or self.browser.config.get("gemini_model", "gemini-3.8-flash")
        self.browser.config["gemini_model"] = model
        from orbit_storage import save_config
        save_config(self.browser.config)
        self.add_message("user", message or self.tr("Фото отправлено на анализ.", "Image sent for analysis."), images)
        self.input.clear()
        self.attachments = []
        self.attachment_label.setText(self.tr("Нет вложений", "No attachments"))
        self.status.setText(self.tr("Gemini думает…", "Gemini is thinking…"))
        self.thread = QThread()
        self.worker = GeminiWorker(self.browser, model, message, images, self.interaction_id)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.failed.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.clear_worker)
        self.thread.start()

    def clear_worker(self):
        self.thread = None
        self.worker = None

    def on_finished(self, data):
        self.interaction_id = data.get("interaction_id") or self.interaction_id
        self.add_message("assistant", data.get("text", ""))
        self.status.setText(self.tr("Готово", "Ready"))

    def on_failed(self, message):
        self.add_message("assistant", self.tr("Не удалось получить ответ Gemini: ", "Gemini request failed: ") + message)
        self.status.setText(self.tr("Ошибка запроса", "Request failed"))

    def refresh_language(self):
        self.language = self.browser.config.get("language", "ru")
        self.input.setPlaceholderText(self.tr("Напишите вопрос…", "Ask Gemini anything…"))
        self.attachment_label.setText(self.tr("Нет вложений", "No attachments"))



class AdminPanelPage(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.role = browser.user.get("role", "user").lower()
        if self.role not in {"helper", "admin"}:
            QLabel("Нет доступа").show()
            return
        self.setObjectName("moderationPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(42, 30, 42, 30)
        layout.setSpacing(12)
        header = QHBoxLayout()
        title = QLabel("Админ-панель" if self.role == "admin" else "Панель Helper")
        title.setObjectName("pageTitle")
        header.addWidget(title); header.addStretch()
        refresh = QPushButton("↻ Обновить")
        refresh.clicked.connect(self.refresh)
        header.addWidget(refresh)
        layout.addLayout(header)
        note = QLabel("Здесь видны только необходимые данные. Роли доступны Admin; Helper может модерировать ник и выдавать достижения.")
        note.setObjectName("muted"); note.setWordWrap(True); layout.addWidget(note)
        self.summary = QLabel("Загрузка…"); self.summary.setObjectName("muted"); layout.addWidget(self.summary)
        self.users = QListWidget(); layout.addWidget(self.users, 1)
        self.status = QLabel(""); self.status.setObjectName("muted"); layout.addWidget(self.status)
        self.refresh(); fade_in(self)

    def refresh(self):
        try:
            h = {"Authorization": f"Bearer {self.browser.token}"}
            r = requests.get(f"{self.browser.API_URL}/api/moderation/users", headers=h, timeout=10)
            if r.status_code != 200:
                self.summary.setText("Нет доступа к панели модерации.")
                return
            users = r.json().get("users", [])
            if self.role == "admin":
                try:
                    s = requests.get(f"{self.browser.API_URL}/api/admin/overview", headers=h, timeout=10).json()
                    self.summary.setText(f"Пользователи: {s.get('users',0)} · Helper: {s.get('helpers',0)} · Admin: {s.get('admins',0)} · Открытых обращений: {s.get('open_tickets',0)}")
                except Exception:
                    self.summary.setText(f"Пользователей: {len(users)}")
            else:
                try:
                    s = requests.get(f"{self.browser.API_URL}/api/helper/overview", headers=h, timeout=10).json()
                    self.summary.setText(f"Пользователей: {len(users)} · Открытых обращений: {s.get('open_tickets',0)}")
                except Exception:
                    self.summary.setText(f"Пользователей: {len(users)}")
            self.users.clear()
            for item in users:
                row = QListWidgetItem(f"{item['display_name']}  ·  @{item['username']}  ·  {item['role']}  ·  {item['title']}")
                row.setData(Qt.ItemDataRole.UserRole, item.get("id"))
                self.users.addItem(row)
            self.users.itemDoubleClicked.connect(self.moderate_user)
        except Exception as exc:
            self.status.setText(f"Ошибка загрузки панели: {exc}")

    def moderate_user(self, item):
        user_id = item.data(Qt.ItemDataRole.UserRole)
        if not user_id:
            return
        target_name = item.text().split("  ·  ")[0]
        menu = QMenu(self)
        rename = menu.addAction("Изменить ник")
        achievement = menu.addAction("Выдать достижение")
        role_action = None
        if self.role == "admin":
            role_action = menu.addAction("Изменить ранг (роль)")
            menu.addSeparator()
            menu.addAction("Открыть полную админку")
        chosen = menu.exec(QCursor.pos())
        if chosen == rename:
            value, ok = QInputDialog.getText(self, "Изменить ник", f"Новый ник для {target_name}:")
            if ok and value.strip():
                r = requests.patch(f"{self.browser.API_URL}/api/moderation/users/{user_id}/display-name", headers={"Authorization": f"Bearer {self.browser.token}"}, json={"display_name": value.strip()}, timeout=10)
                self.status.setText("Ник изменён." if r.ok else (r.json().get("detail", "Не удалось изменить ник") if r.content else "Не удалось изменить ник"))
                self.refresh()
        elif chosen == achievement:
            keys = ["first_launch", "explorer", "collector", "navigator", "notes"]
            labels = ["Первый шаг", "Исследователь", "Коллекционер", "Навигатор", "Архивариус"]
            value, ok = QInputDialog.getItem(self, "Выдать достижение", "Достижение:", labels, 0, False)
            if ok:
                key = keys[labels.index(value)]
                r = requests.patch(f"{self.browser.API_URL}/api/moderation/users/{user_id}/achievement", headers={"Authorization": f"Bearer {self.browser.token}"}, json={"achievement_key": key}, timeout=10)
                self.status.setText("Достижение выдано." if r.ok else (r.json().get("detail", "Не удалось выдать достижение") if r.content else "Не удалось выдать достижение"))
                self.refresh()
        elif role_action is not None and chosen == role_action:
            value, ok = QInputDialog.getItem(self, "Изменить ранг", "Роль:", ["user", "helper", "admin"], 0, False)
            if ok:
                r = requests.patch(f"{self.browser.API_URL}/api/admin/users/{user_id}/role", headers={"Authorization": f"Bearer {self.browser.token}"}, json={"role": value}, timeout=10)
                self.status.setText("Роль изменена." if r.ok else (r.json().get("detail", "Не удалось изменить роль") if r.content else "Не удалось изменить роль"))
                self.refresh()


class SupportTicketDialog(QDialog):
    def __init__(self, parent=None, lang="ru"):
        super().__init__(parent)
        self.lang = lang
        self.setWindowTitle("Связаться с поддержкой" if lang == "ru" else "Contact support")
        self.setMinimumSize(520, 380)
        layout = QVBoxLayout(self)
        title = QLabel("Сообщить о проблеме" if lang == "ru" else "Report a problem")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.subject = QLineEdit()
        self.subject.setPlaceholderText("Например: не сохраняется профиль" if lang == "ru" else "For example: profile is not saving")
        self.message = QTextEdit()
        self.message.setPlaceholderText("Опишите проблему как можно понятнее…" if lang == "ru" else "Describe the issue as clearly as possible…")
        form = QFormLayout()
        form.addRow("Тема" if lang == "ru" else "Subject", self.subject)
        form.addRow("Сообщение" if lang == "ru" else "Message", self.message)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        cancel = QPushButton("Отмена" if lang == "ru" else "Cancel")
        send = QPushButton("Отправить" if lang == "ru" else "Send")
        send.setProperty("accent", True)
        cancel.clicked.connect(self.reject)
        send.clicked.connect(self.accept)
        buttons.addStretch()
        buttons.addWidget(cancel)
        buttons.addWidget(send)
        layout.addLayout(buttons)

    def values(self):
        return self.subject.text().strip(), self.message.toPlainText().strip()


class SupportPage(QWidget):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser
        self.lang = browser.config.get("language", "ru")
        self.tickets = []
        self.build()
        self.load_tickets()
        if browser.user.get("role", "user").lower() in {"helper", "admin"}:
            self.load_queue()
        self.sync_timer = QTimer(self)
        self.sync_timer.setInterval(3000)
        self.sync_timer.timeout.connect(self.sync_support)
        self.sync_timer.start()
        fade_in(self, 220)

    def tr(self, ru, en):
        return ru if self.browser.config.get("language", "ru") == "ru" else en

    def build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 28, 36, 30)
        layout.setSpacing(12)
        title = QLabel(self.tr("Orbit Помощь", "Orbit Support"))
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        sub = QLabel(self.tr(
            "Задайте вопрос, сообщите об ошибке или попросите помощника разобраться. Между обращениями стоит короткий антиспам-кд.",
            "Ask a question, report a bug, or ask a helper to investigate. A short anti-spam cooldown protects the support queue."
        ))
        sub.setObjectName("homepageSub")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        actions = QHBoxLayout()
        new_ticket = QPushButton("＋ " + self.tr("Новое обращение", "New request"))
        new_ticket.setProperty("accent", True)
        new_ticket.clicked.connect(self.new_ticket)
        actions.addWidget(new_ticket)
        refresh = QPushButton("↻ " + self.tr("Обновить", "Refresh"))
        refresh.clicked.connect(self.load_tickets)
        actions.addWidget(refresh)
        actions.addStretch()
        layout.addLayout(actions)

        self.list = QListWidget()
        self.list.setObjectName("supportList")
        layout.addWidget(self.list, 1)

        role = self.browser.user.get("role", "user").lower()
        if role in {"helper", "admin"}:
            sep = QLabel(self.tr("Очередь помощи для Helper / Admin", "Helper / Admin support queue"))
            sep.setObjectName("section")
            layout.addWidget(sep)
            self.queue = QListWidget()
            self.queue.setObjectName("supportQueue")
            layout.addWidget(self.queue, 1)
            self.queue.itemClicked.connect(self.reply_selected)
        else:
            self.queue = None

        self.status = QLabel("")
        self.status.setObjectName("muted")
        layout.addWidget(self.status)

    def sync_support(self):
        # Быстрая синхронизация: обращения и ответы обновляются без перезапуска страницы.
        if not self.isVisible():
            return
        self.load_tickets()
        if self.queue is not None:
            self.load_queue()

    def new_ticket(self):
        dialog = SupportTicketDialog(self, self.browser.config.get("language", "ru"))
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        subject, message = dialog.values()
        if not subject or not message:
            QMessageBox.warning(self, "Orbit", self.tr("Заполните тему и сообщение.", "Fill in the subject and message."))
            return
        try:
            r = requests.post(
                f"{self.browser.API_URL}/api/support/tickets",
                json={"subject": subject, "message": message},
                headers={"Authorization": f"Bearer {self.browser.token}"},
                timeout=15,
            )
            if r.status_code == 429:
                QMessageBox.information(self, "Orbit", self.tr("Слишком часто. Подождите немного перед следующим обращением.", "Too fast. Please wait a little before sending another request."))
                return
            if r.status_code >= 400:
                detail = r.json().get("detail", r.text) if r.headers.get("content-type", "").startswith("application/json") else r.text
                raise RuntimeError(str(detail))
            self.status.setText(self.tr("Обращение отправлено помощникам.", "Your request was sent to the support team."))
            self.load_tickets()
        except Exception as exc:
            self.status.setText(self.tr("Не удалось отправить обращение: ", "Could not send request: ") + str(exc))

    def closeEvent(self, event):
        if hasattr(self, "sync_timer"):
            self.sync_timer.stop()
        super().closeEvent(event)

    def ticket_text(self, ticket):
        status_map = {"open": self.tr("Открыто", "Open"), "pending": self.tr("В работе", "In progress"), "closed": self.tr("Закрыто", "Closed")}
        text = f"{ticket.get('subject','')}  ·  {status_map.get(ticket.get('status'), ticket.get('status',''))}\n{ticket.get('message','')}"
        if ticket.get("reply"):
            text += "\n\n" + self.tr("Ответ: ", "Reply: ") + ticket["reply"]
        return text

    def load_tickets(self):
        try:
            r = requests.get(f"{self.browser.API_URL}/api/support/my", headers={"Authorization": f"Bearer {self.browser.token}"}, timeout=12)
            if r.status_code != 200:
                return
            self.tickets = r.json().get("tickets", [])
            self.list.clear()
            for t in self.tickets:
                item = QListWidgetItem(self.ticket_text(t))
                self.list.addItem(item)
        except Exception:
            pass

    def load_queue(self):
        if self.queue is None:
            return
        try:
            r = requests.get(f"{self.browser.API_URL}/api/support/tickets", headers={"Authorization": f"Bearer {self.browser.token}"}, timeout=12)
            if r.status_code != 200:
                return
            self.queue.clear()
            for t in r.json().get("tickets", []):
                item = QListWidgetItem(f"#{t['id']} · {t['display_name']} · {t['subject']}\n{t['message']}")
                item.setData(Qt.ItemDataRole.UserRole, t)
                self.queue.addItem(item)
        except Exception:
            pass

    def reply_selected(self, item):
        ticket = item.data(Qt.ItemDataRole.UserRole) or {}
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("Ответ пользователю", "Reply to user"))
        dialog.setMinimumSize(520, 360)
        layout = QVBoxLayout(dialog)
        info = QLabel(f"#{ticket.get('id')} · {ticket.get('display_name','') }\n{ticket.get('message','')}")
        info.setWordWrap(True)
        layout.addWidget(info)
        reply = QTextEdit()
        reply.setPlaceholderText(self.tr("Ваш ответ…", "Your reply…"))
        layout.addWidget(reply, 1)
        status_combo = QComboBox()
        status_combo.addItems(["open", "pending", "closed"])
        layout.addWidget(status_combo)
        send = QPushButton(self.tr("Ответить", "Reply"))
        send.setProperty("accent", True)
        layout.addWidget(send)
        send.clicked.connect(dialog.accept)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            r = requests.patch(
                f"{self.browser.API_URL}/api/support/tickets/{ticket.get('id')}",
                json={"message": reply.toPlainText().strip(), "status": status_combo.currentText()},
                headers={"Authorization": f"Bearer {self.browser.token}"}, timeout=15)
            if r.status_code >= 400:
                raise RuntimeError(r.text)
            self.load_queue(); self.load_tickets()
        except Exception as exc:
            self.status.setText(str(exc))


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
        row.setContentsMargins(18, 12, 14, 12)
        card.setMinimumHeight(76)
        texts = QVBoxLayout()
        name = QLabel(title)
        name.setObjectName("settingTitle")
        desc = QLabel(description)
        desc.setObjectName("settingDescription")
        desc.setWordWrap(True)
        desc.setMinimumHeight(34)
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
        for label, data in [("Orbit", "orbit"), ("Google", "google"), ("Bing", "bing"), ("DuckDuckGo", "duckduckgo")]:
            engine.addItem(label, data)
        idx = engine.findData(self.browser.config.get("search_engine", "orbit"))
        engine.setCurrentIndex(idx if idx >= 0 else 0)
        engine.currentIndexChanged.connect(self.save_engine)
        self.add_card("Поисковая система", "Orbit выбран по умолчанию. Выберите другой поисковик, если он нужен.", engine)
        vpn = QPushButton("Включено" if self.browser.config.get("require_vpn", False) else "Выключено")
        vpn.clicked.connect(lambda: self.toggle_bool("require_vpn", vpn))
        self.add_card("Требовать VPN", "Запрещает Orbit открывать внешние сайты, если в Windows не найден распространённый VPN-адаптер. Выключено по умолчанию.", vpn)

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
            self.browser.home.engine_hint.setText({"google":"Google","bing":"Bing","duckduckgo":"DuckDuckGo","orbit":"Orbit"}.get(self.browser.config["search_engine"], "Orbit"))

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



# extension method injected for SettingsPage
def _settings_toggle_nav_hidden(self, key, button):
    hidden = set(self.browser.config.get("hidden_nav", []))
    if key in hidden:
        hidden.remove(key); button.setText("Показывать")
    else:
        hidden.add(key); button.setText("Скрыть")
    self.browser.config["hidden_nav"] = sorted(hidden)
    from orbit_storage import save_config
    save_config(self.browser.config)
    self.browser.apply_language()

SettingsPage.toggle_nav_hidden = _settings_toggle_nav_hidden
