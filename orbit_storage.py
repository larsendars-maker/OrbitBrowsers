import json
import os
from pathlib import Path

APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "OrbitBrowser"
CONFIG_DIR = APP_DIR / "config"
DATA_DIR = APP_DIR / "data"
CONFIG_FILE = CONFIG_DIR / "config.json"
BOOKMARKS_FILE = DATA_DIR / "bookmarks.json"
NOTES_FILE = DATA_DIR / "notes.json"
SHORTCUTS_FILE = DATA_DIR / "shortcuts.json"
AVATAR_FILE = DATA_DIR / "profile_avatar.png"
PROFILE_FILE = DATA_DIR / "profile.json"

DEFAULT_CONFIG = {
    "theme": "VOID",
    "search_engine": "google",
    "site_theming": True,
    "animations": True,
    "weather_city": "Москва",
    "weather_country": "Россия",
    "weather_timezone": "auto",
    "weather_latitude": None,
    "weather_longitude": None,
    "auto_update": True,
    "avatar_path": "",
    "language": "ru",
    "shortcuts_cleaned": False,
    "stats_sessions": 0,
    "stats_pages": 0,
}

DEFAULT_SHORTCUTS = [
    {"title": "YouTube", "url": "https://www.youtube.com", "icon": "▶", "builtin": True},
    {"title": "Discord", "url": "https://discord.com", "icon": "◉", "builtin": True},
    {"title": "GitHub", "url": "https://github.com", "icon": "◒", "builtin": True},
    {"title": "Spotify", "url": "https://open.spotify.com", "icon": "♪", "builtin": True},
    {"title": "Twitch", "url": "https://www.twitch.tv", "icon": "ϟ", "builtin": True},
    {"title": "Telegram", "url": "https://web.telegram.org", "icon": "➤", "builtin": True},
]



def ensure_storage():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path, default):
    ensure_storage()
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def write_json(path, data):
    ensure_storage()
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_config():
    config = read_json(CONFIG_FILE, {})
    result = DEFAULT_CONFIG.copy()
    if isinstance(config, dict):
        result.update(config)
    if result.get("theme") not in {"VOID", "ICE", "MIDNIGHT", "EMBER"}:
        result["theme"] = "VOID"
    write_json(CONFIG_FILE, result)
    return result


def save_config(config):
    write_json(CONFIG_FILE, config)


def save_local_profile(user):
    if isinstance(user, dict):
        write_json(PROFILE_FILE, user)


def load_local_profile():
    value = read_json(PROFILE_FILE, {})
    return value if isinstance(value, dict) else {}


def load_bookmarks():
    value = read_json(BOOKMARKS_FILE, [])
    return value if isinstance(value, list) else []


def save_bookmarks(items):
    write_json(BOOKMARKS_FILE, items)


def add_bookmark(title, url):
    items = load_bookmarks()
    if any(x.get("url") == url for x in items):
        return items
    items.insert(0, {"title": title or url, "url": url})
    save_bookmarks(items)
    return items


def load_notes():
    value = read_json(NOTES_FILE, [])
    return value if isinstance(value, list) else []


def save_notes(items):
    write_json(NOTES_FILE, items)


def load_shortcuts():
    value = read_json(SHORTCUTS_FILE, None)
    if not isinstance(value, list):
        value = DEFAULT_SHORTCUTS.copy()
    # Новая версия Orbit не навязывает встроенные сайты в быстром доступе.
    # Удаляем старые встроенные плитки один раз, сохраняя пользовательские.
    config = read_json(CONFIG_FILE, DEFAULT_CONFIG.copy())
    if not config.get("shortcuts_cleaned", False):
        value = [item for item in value if not item.get("builtin")]
        config["shortcuts_cleaned"] = True
        write_json(CONFIG_FILE, config)
    save_shortcuts(value)
    return value


def save_shortcuts(items):
    write_json(SHORTCUTS_FILE, items)


def add_shortcut(title, url, icon="↗"):
    items = load_shortcuts()
    items.append({"title": title.strip(), "url": url.strip(), "icon": icon, "builtin": False})
    save_shortcuts(items)
    return items


def remove_shortcut(index):
    items = load_shortcuts()
    if 0 <= index < len(items) and not items[index].get("builtin"):
        items.pop(index)
        save_shortcuts(items)
    return items
