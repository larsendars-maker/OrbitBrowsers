# Orbit Browser 2.3

Быстрый, единый и настраиваемый браузер Orbit.

## Новое в 1.8
- Snake после смерти автоматически сбрасывается в новое состояние.
- Snake принимает WASD и стрелки.
- Block Blast получил drag-and-drop для фигур.
- После размещения фигуры сразу выдаётся новая случайная фигура.
- Превью размещения показывает корректную/некорректную позицию.
- Game Over Block Blast автоматически начинает новую партию.
- Мини-игры синхронизированы для сайта, Windows и Android offline-режима.

Windows и Android собираются через GitHub Actions.

## Orbit 2.3

Orbit 2.3 объединяет Windows, Android, сайт и Orbit Core в единую релизную версию.

Default search engine: **Google**.

Windows and Android builds are produced by GitHub Actions.


## Orbit 2.3

### Быстродействие
Orbit запускает интерфейс сразу и выполняет сеть, синхронизацию и update-check в фоне. Пользовательский переключатель медленного режима удалён.

### Восстановление
Последние веб-вкладки сохраняются, закрытая вкладка может быть восстановлена через `Ctrl+Shift+T`. Локальные JSON-файлы сохраняются атомарно с backup-копией.

### Клавиатура
`Ctrl+L`, `Ctrl+T`, `Ctrl+W`, `Ctrl+Shift+T`, `Ctrl+H`, `Ctrl+D`, `Ctrl+J`, `Ctrl+K`, `Alt+Left`, `Alt+Right`.

### Release
Windows Actions создаёт только один `OrbitBrowser.exe`. Android Actions создаёт только один `OrbitBrowser.apk`. Отдельный Security workflow проверяет секреты и Python smoke tests.

## Orbit 2.3

Фокус релиза — не новые декоративные экраны, а **Core / Performance / Storage**:

- SQLite (`data/orbit.db`) для bookmarks/history/notes/downloads/shortcuts.
- WAL + индексы для быстрого локального чтения.
- авто-миграция с JSON из предыдущих версий.
- `Ctrl+K` — Command Center.
- `/new-tab`, `/settings`, `/history`, `/downloads`, `/clear-cache`, `/theme VOID` и другие команды.
- расширенное восстановление закрытых вкладок.
- контекстное меню вкладок и pin.
- единая `PerformancePolicy` для QtWebEngine.

Пользовательские данные остаются в `%LOCALAPPDATA%\\OrbitBrowser`, а исходники и build-инструменты не являются обязательной частью запуска готового приложения.
