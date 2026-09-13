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
    "search_engine": "https://www.google.com/search?q=",
    "homepage": "orbit://home",
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
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def write_json(path, data):
    ensure_storage()
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def load_config():
    config = read_json(CONFIG_FILE, {})
    if not isinstance(config, dict):
        config = {}
    result = DEFAULT_CONFIG.copy()
    result.update(config)
    write_json(CONFIG_FILE, result)
    return result


def save_config(config):
    write_json(CONFIG_FILE, config)


def load_bookmarks():
    data = read_json(BOOKMARKS_FILE, [])
    return data if isinstance(data, list) else []


def save_bookmarks(bookmarks):
    write_json(BOOKMARKS_FILE, bookmarks)


def add_bookmark(title, url):
    bookmarks = load_bookmarks()
    if not any(item.get("url") == url for item in bookmarks):
        bookmarks.insert(0, {"title": title or url, "url": url})
        save_bookmarks(bookmarks)
    return bookmarks


def load_notes():
    data = read_json(NOTES_FILE, [])
    return data if isinstance(data, list) else []


def save_notes(notes):
    write_json(NOTES_FILE, notes)
