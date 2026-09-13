import json
import os
from pathlib import Path

APP_DIR = Path(
os.environ.get(
"LOCALAPPDATA",
Path.home(),
)
) / "OrbitBrowser"

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
"compact_mode": False,
}

def ensure_storage():
CONFIG_DIR.mkdir(
parents=True,
exist_ok=True,
)

```
DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)
```

def read_json(path, default):
ensure_storage()

```
if not path.exists():
    return default

try:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)

except Exception:
    return default
```

def write_json(path, data):
ensure_storage()

```
with path.open(
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        data,
        file,
        ensure_ascii=False,
        indent=4,
    )
```

def load_config():
config = read_json(
CONFIG_FILE,
{},
)

```
if not isinstance(config, dict):
    config = {}

result = DEFAULT_CONFIG.copy()
result.update(config)

write_json(
    CONFIG_FILE,
    result,
)

return result
```

def save_config(config):
write_json(
CONFIG_FILE,
config,
)

def load_bookmarks():
data = read_json(
BOOKMARKS_FILE,
[],
)

```
return data if isinstance(data, list) else []
```

def save_bookmarks(bookmarks):
save_data = []

```
for item in bookmarks:
    if not isinstance(item, dict):
        continue

    save_data.append(
        {
            "title": str(
                item.get("title", "")
            ),
            "url": str(
                item.get("url", "")
            ),
        }
    )

write_json(
    BOOKMARKS_FILE,
    save_data,
)
```

def add_bookmark(
title,
url,
):
bookmarks = load_bookmarks()

```
for item in bookmarks:
    if item.get("url") == url:
        return bookmarks

bookmarks.insert(
    0,
    {
        "title": title or url,
        "url": url,
    },
)

save_bookmarks(
    bookmarks,
)

return bookmarks
```

def remove_bookmark(url):
bookmarks = [
item
for item in load_bookmarks()
if item.get("url") != url
]

```
save_bookmarks(
    bookmarks,
)

return bookmarks
```

def load_notes():
data = read_json(
NOTES_FILE,
[],
)

```
return data if isinstance(data, list) else []
```

def save_notes(notes):
write_json(
NOTES_FILE,
notes,
)
