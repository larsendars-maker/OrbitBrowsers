import json
import os
import sqlite3
import time
from pathlib import Path
from threading import RLock

APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "OrbitBrowser"
CONFIG_DIR = APP_DIR / "config"
DATA_DIR = APP_DIR / "data"
CONFIG_FILE = CONFIG_DIR / "config.json"
DB_FILE = DATA_DIR / "orbit.db"
BOOKMARKS_FILE = DATA_DIR / "bookmarks.json"  # legacy compatibility
NOTES_FILE = DATA_DIR / "notes.json"
SHORTCUTS_FILE = DATA_DIR / "shortcuts.json"
HISTORY_FILE = DATA_DIR / "history.json"
DOWNLOADS_FILE = DATA_DIR / "downloads.json"
AVATAR_FILE = DATA_DIR / "profile_avatar.png"
PROFILE_FILE = DATA_DIR / "profile.json"

DEFAULT_CONFIG = {
    "theme": "VOID",
    "config_version": 8,
    "performance_mode": "performance",
    "crash_recovery": True,
    "session_tabs": [],
    "last_closed_url": "",
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
    "unlocked_titles": [],
    "equipped_title": "Explorer",
    "proxy_url": "",
    "require_vpn": False,
    "hidden_nav": [],
    "first_run_guide_seen": False,
    "command_palette_recent": [],
    "tab_groups": [],
    "notifications_enabled": True,
    "compact_tabs": True,
}

DEFAULT_SHORTCUTS = []
_DB_LOCK = RLock()
_DB_READY = False


def ensure_storage():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (APP_DIR / "profiles").mkdir(parents=True, exist_ok=True)
    (APP_DIR / "themes").mkdir(parents=True, exist_ok=True)
    (APP_DIR / "notes").mkdir(parents=True, exist_ok=True)
    (APP_DIR / "workspaces").mkdir(parents=True, exist_ok=True)
    (APP_DIR / "downloads").mkdir(parents=True, exist_ok=True)
    (APP_DIR / "cache").mkdir(parents=True, exist_ok=True)
    (APP_DIR / "logs").mkdir(parents=True, exist_ok=True)


def _conn():
    ensure_storage()
    conn = sqlite3.connect(DB_FILE, timeout=8, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _db_exec(sql, params=(), fetch=False, many=False):
    global _DB_READY
    with _DB_LOCK:
        conn = _conn()
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS bookmarks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, url TEXT NOT NULL UNIQUE, created_at REAL NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL, created_at REAL NOT NULL, updated_at REAL NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS shortcuts (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, url TEXT NOT NULL, icon TEXT NOT NULL, builtin INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, url TEXT NOT NULL, timestamp REAL NOT NULL)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history(timestamp DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_history_url ON history(url)")
            conn.execute("CREATE TABLE IF NOT EXISTS downloads (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL, url TEXT NOT NULL, path TEXT NOT NULL UNIQUE, state TEXT NOT NULL, size INTEGER NOT NULL DEFAULT 0, timestamp REAL NOT NULL, extra TEXT NOT NULL DEFAULT '{}')")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_downloads_timestamp ON downloads(timestamp DESC)")
            conn.commit()
            _DB_READY = True
            cur = conn.executemany(sql, params) if many else conn.execute(sql, params)
            if fetch:
                return cur.fetchall()
            conn.commit()
            return None
        finally:
            conn.close()


def initialize_database():
    ensure_storage()
    _db_exec("SELECT 1")
    marker = read_json(DATA_DIR / "storage_migration.json", {})
    if marker.get("sqlite_v1"):
        return
    # One-time migration from v1.10/v1.11 JSON stores.
    # Mark before calling public helpers to avoid recursive initialization during migration.
    write_json(DATA_DIR / "storage_migration.json", {"sqlite_v1": True, "migrated_at": time.time()})
    bookmarks = _legacy_json(BOOKMARKS_FILE, [])
    if bookmarks:
        save_bookmarks(bookmarks)
    notes = _legacy_json(NOTES_FILE, [])
    if notes:
        save_notes(notes)
    shortcuts = _legacy_json(SHORTCUTS_FILE, [])
    if shortcuts:
        save_shortcuts(shortcuts)
    history = _legacy_json(HISTORY_FILE, [])
    if history:
        save_history(history)
    downloads = _legacy_json(DOWNLOADS_FILE, [])
    if downloads:
        save_downloads(downloads)


def _legacy_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def read_json(path, default):
    ensure_storage()
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path, data):
    ensure_storage()
    tmp = path.with_suffix(path.suffix + ".tmp")
    backup = path.with_suffix(path.suffix + ".bak")
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    tmp.write_text(payload, encoding="utf-8")
    if path.exists():
        try:
            path.replace(backup)
        except Exception:
            pass
    tmp.replace(path)


def load_config():
    config = read_json(CONFIG_FILE, {})
    result = DEFAULT_CONFIG.copy()
    if isinstance(config, dict):
        result.update(config)
    if result.get("theme") not in {"VOID", "ICE", "BLUE", "PURPLE", "CYBER", "SUNSET", "EMERALD", "RED"}:
        result["theme"] = "VOID"
    if result.get("search_engine") not in {"google", "bing", "duckduckgo", "yandex"}:
        result["search_engine"] = "google"
    result["performance_mode"] = "performance"
    result["config_version"] = max(8, int(result.get("config_version", 1) or 1))
    write_json(CONFIG_FILE, result)
    initialize_database()
    return result


def save_config(config):
    config = dict(config or {})
    config["performance_mode"] = "performance"
    config["config_version"] = max(8, int(config.get("config_version", 8) or 8))
    write_json(CONFIG_FILE, config)


def save_local_profile(user):
    if isinstance(user, dict):
        write_json(PROFILE_FILE, user)


def load_local_profile():
    value = read_json(PROFILE_FILE, {})
    return value if isinstance(value, dict) else {}


def _rows_to_items(rows):
    return [dict(row) for row in rows]


def load_bookmarks():
    initialize_database()
    rows = _db_exec("SELECT title, url, created_at FROM bookmarks ORDER BY id DESC", fetch=True)
    return _rows_to_items(rows)


def save_bookmarks(items):
    initialize_database()
    items = items if isinstance(items, list) else []
    with _DB_LOCK:
        conn = _conn()
        try:
            conn.execute("DELETE FROM bookmarks")
            conn.executemany(
                "INSERT OR IGNORE INTO bookmarks(title,url,created_at) VALUES(?,?,?)",
                [(str(x.get("title", "")), str(x.get("url", "")), float(x.get("created_at", time.time()))) for x in items if isinstance(x, dict) and x.get("url")]
            )
            conn.commit()
        finally:
            conn.close()


def add_bookmark(title, url):
    initialize_database()
    url = str(url or "").strip()
    if not url:
        return load_bookmarks()
    with _DB_LOCK:
        conn = _conn()
        try:
            conn.execute("INSERT OR IGNORE INTO bookmarks(title,url,created_at) VALUES(?,?,?)", (str(title or url), url, time.time()))
            conn.commit()
        finally:
            conn.close()
    return load_bookmarks()


def load_notes():
    initialize_database()
    rows = _db_exec("SELECT payload FROM notes ORDER BY id DESC", fetch=True)
    out = []
    for row in rows:
        try:
            out.append(json.loads(row[0]))
        except Exception:
            continue
    return out


def save_notes(items):
    initialize_database()
    items = items if isinstance(items, list) else []
    now = time.time()
    with _DB_LOCK:
        conn = _conn()
        try:
            conn.execute("DELETE FROM notes")
            conn.executemany(
                "INSERT INTO notes(payload,created_at,updated_at) VALUES(?,?,?)",
                [(json.dumps(x, ensure_ascii=False), float(x.get("created_at", now)) if isinstance(x, dict) else now, float(x.get("updated_at", now)) if isinstance(x, dict) else now) for x in items]
            )
            conn.commit()
        finally:
            conn.close()


def load_shortcuts():
    initialize_database()
    rows = _db_exec("SELECT title,url,icon,builtin FROM shortcuts ORDER BY id DESC", fetch=True)
    value = [{"title": r[0], "url": r[1], "icon": r[2], "builtin": bool(r[3])} for r in rows]
    config = read_json(CONFIG_FILE, DEFAULT_CONFIG.copy())
    if not config.get("shortcuts_cleaned", False):
        value = [item for item in value if not item.get("builtin")]
        config["shortcuts_cleaned"] = True
        write_json(CONFIG_FILE, config)
        save_shortcuts(value)
    return value


def save_shortcuts(items):
    initialize_database()
    items = items if isinstance(items, list) else []
    with _DB_LOCK:
        conn = _conn()
        try:
            conn.execute("DELETE FROM shortcuts")
            conn.executemany("INSERT INTO shortcuts(title,url,icon,builtin,created_at) VALUES(?,?,?,?,?)", [(str(x.get("title", "")), str(x.get("url", "")), str(x.get("icon", "↗")), int(bool(x.get("builtin"))), time.time()) for x in items if isinstance(x, dict)])
            conn.commit()
        finally:
            conn.close()


def add_shortcut(title, url, icon="↗"):
    items = load_shortcuts()
    items.append({"title": str(title).strip(), "url": str(url).strip(), "icon": icon, "builtin": False})
    save_shortcuts(items)
    return items


def remove_shortcut(index):
    items = load_shortcuts()
    if 0 <= index < len(items) and not items[index].get("builtin"):
        items.pop(index)
        save_shortcuts(items)
    return items


def load_history(limit=1000):
    initialize_database()
    limit = max(1, min(int(limit or 1000), 10000))
    rows = _db_exec("SELECT title,url,timestamp FROM history ORDER BY timestamp DESC LIMIT ?", (limit,), fetch=True)
    return _rows_to_items(rows)[::-1]


def save_history(items):
    initialize_database()
    items = items[-2000:] if isinstance(items, list) else []
    with _DB_LOCK:
        conn = _conn()
        try:
            conn.execute("DELETE FROM history")
            conn.executemany("INSERT INTO history(title,url,timestamp) VALUES(?,?,?)", [(str(x.get("title", x.get("url", ""))), str(x.get("url", "")), float(x.get("timestamp", time.time()))) for x in items if isinstance(x, dict) and x.get("url")])
            conn.commit()
        finally:
            conn.close()


def add_history(title, url):
    initialize_database()
    title = str(title or url or "").strip()
    url = str(url or "").strip()
    if not url or url.startswith("orbit://"):
        return load_history()
    now = time.time()
    with _DB_LOCK:
        conn = _conn()
        try:
            conn.execute("DELETE FROM history WHERE url=?", (url,))
            conn.execute("INSERT INTO history(title,url,timestamp) VALUES(?,?,?)", (title, url, now))
            conn.execute("DELETE FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY timestamp DESC LIMIT 2000)")
            conn.commit()
        finally:
            conn.close()
    return load_history()


def load_downloads():
    initialize_database()
    rows = _db_exec("SELECT filename,url,path,state,size,timestamp,extra FROM downloads ORDER BY timestamp DESC LIMIT 500", fetch=True)
    out = []
    for r in rows:
        item = {"filename": r[0], "url": r[1], "path": r[2], "state": r[3], "size": r[4], "timestamp": r[5]}
        try:
            item.update(json.loads(r[6] or "{}"))
        except Exception:
            pass
        out.append(item)
    return out


def save_downloads(items):
    initialize_database()
    items = items[-500:] if isinstance(items, list) else []
    with _DB_LOCK:
        conn = _conn()
        try:
            conn.execute("DELETE FROM downloads")
            for x in items:
                if not isinstance(x, dict) or not x.get("path"):
                    continue
                base = {k: v for k, v in x.items() if k not in {"filename", "url", "path", "state", "size", "timestamp"}}
                conn.execute("INSERT OR REPLACE INTO downloads(filename,url,path,state,size,timestamp,extra) VALUES(?,?,?,?,?,?,?)", (str(x.get("filename", "")), str(x.get("url", "")), str(x.get("path", "")), str(x.get("state", "completed")), int(x.get("size", 0) or 0), float(x.get("timestamp", time.time())), json.dumps(base, ensure_ascii=False)))
            conn.commit()
        finally:
            conn.close()


def add_download(filename, url, path, state="completed", size=0):
    initialize_database()
    payload = (str(filename), str(url), str(path), str(state), int(size or 0), time.time(), "{}")
    with _DB_LOCK:
        conn = _conn()
        try:
            conn.execute("INSERT OR REPLACE INTO downloads(filename,url,path,state,size,timestamp,extra) VALUES(?,?,?,?,?,?,?)", payload)
            conn.commit()
        finally:
            conn.close()
    return load_downloads()


def update_download(old_path, **changes):
    initialize_database()
    items = load_downloads()
    for item in items:
        if item.get("path") == old_path:
            item.update({k: v for k, v in changes.items() if v is not None})
            save_downloads(items)
            break
    return load_downloads()


def remove_download(path):
    initialize_database()
    with _DB_LOCK:
        conn = _conn()
        try:
            conn.execute("DELETE FROM downloads WHERE path=?", (str(path),))
            conn.commit()
        finally:
            conn.close()
    return load_downloads()


def build_sync_bundle(config=None, user=None):
    return {
        "version": 2,
        "storage": "sqlite",
        "user": user or {},
        "config": config or load_config(),
        "bookmarks": load_bookmarks(),
        "notes": load_notes(),
        "shortcuts": load_shortcuts(),
        "history": load_history(500),
        "downloads": load_downloads()[:200],
    }


def sync_state_signature(bundle):
    import hashlib
    raw = json.dumps(bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def apply_sync_bundle(bundle, config=None):
    if not isinstance(bundle, dict):
        return
    remote_config = bundle.get("config")
    if isinstance(remote_config, dict):
        local = load_config()
        local.update(remote_config)
        save_config(local)
    if isinstance(bundle.get("bookmarks"), list):
        save_bookmarks(bundle["bookmarks"])
    if isinstance(bundle.get("notes"), list):
        save_notes(bundle["notes"])
    if isinstance(bundle.get("shortcuts"), list):
        save_shortcuts(bundle["shortcuts"])
    if isinstance(bundle.get("history"), list):
        save_history(bundle["history"])
    if isinstance(bundle.get("downloads"), list):
        save_downloads(bundle["downloads"])
