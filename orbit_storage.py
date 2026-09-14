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
HISTORY_FILE = DATA_DIR / "history.json"
DOWNLOADS_FILE = DATA_DIR / "downloads.json"
AVATAR_FILE = DATA_DIR / "profile_avatar.png"
PROFILE_FILE = DATA_DIR / "profile.json"

DEFAULT_CONFIG = {
    "theme": "VOID",
    "search_engine": "orbit",
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
    "unlocked_titles": [],
    "equipped_title": "Explorer",
    "proxy_url": "",
    "require_vpn": False,
    "hidden_nav": [],
}

DEFAULT_SHORTCUTS = []


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
    if result.get("search_engine") not in {"google", "bing", "duckduckgo", "orbit"}:
        result["search_engine"] = "orbit"
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


def load_history():
    value = read_json(HISTORY_FILE, [])
    return value if isinstance(value, list) else []


def save_history(items):
    save = items[-1000:] if isinstance(items, list) else []
    write_json(HISTORY_FILE, save)


def add_history(title, url):
    title = (title or url or "").strip()
    url = (url or "").strip()
    if not url or url.startswith("orbit://"):
        return load_history()
    items = load_history()
    items = [x for x in items if x.get("url") != url]
    items.append({"title": title, "url": url, "timestamp": __import__("time").time()})
    save_history(items)
    return items


def load_downloads():
    value = read_json(DOWNLOADS_FILE, [])
    return value if isinstance(value, list) else []


def save_downloads(items):
    write_json(DOWNLOADS_FILE, items[-500:] if isinstance(items, list) else [])


def add_download(filename, url, path, state="completed", size=0):
    items = load_downloads()
    items.insert(0, {"filename": filename, "url": url, "path": path, "state": state, "size": int(size or 0), "timestamp": __import__("time").time()})
    save_downloads(items)
    return items


def update_download(old_path, **changes):
    items = load_downloads()
    for item in items:
        if item.get("path") == old_path:
            item.update({k: v for k, v in changes.items() if v is not None})
            break
    save_downloads(items)
    return items


def remove_download(path):
    items = [x for x in load_downloads() if x.get("path") != path]
    save_downloads(items)
    return items
