import json
import os
from pathlib import Path

APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "OrbitBrowser"
CONFIG_DIR = APP_DIR / "config"
DATA_DIR = APP_DIR / "data"
CONFIG_FILE = CONFIG_DIR / "config.json"
BOOKMARKS_FILE = DATA_DIR / "bookmarks.json"
NOTES_FILE = DATA_DIR / "notes.json"

DEFAULT_CONFIG = {
    "theme": "VOID",
    "search_engine": "orbit",
    "site_theming": True,
    "animations": True,
}


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
