# Orbit Browser Changelog

## 1.12.1 — Build Fix

- Исправлена Kotlin-ошибка в `MainActivity.kt` из-за затенения переменной `text`.
- Android version metadata приведены к 1.12.
- Исправлена Windows PyInstaller-сборка: assets/icon/version file передаются абсолютными путями, чтобы `--specpath build_spec` не искал `build_spec/assets`.
- Inno Setup обновлён до 1.12.
- Сайт обновлён до 1.12, включая прямые Windows/Android download links, games pages и changelog.

# Orbit Browser Changelog

## 1.11 — Final Polish

### Performance
- Fast mode is now the default and the only user-facing performance mode.
- UI is shown before network/session synchronization completes.
- Sync and update checks remain background operations.
- Chromium cache and renderer configuration tuned for fast navigation.

### Browser UX
- Restored a complete single-window internal page/tab architecture.
- Added Ctrl+L, Ctrl+T, Ctrl+W, Ctrl+Shift+T, Ctrl+H, Ctrl+D, Ctrl+J, Ctrl+K, Alt+Left and Alt+Right.
- Added last-closed-tab recovery.
- Added session tab persistence and restore.
- Ctrl+D saves the current page to bookmarks.
- `target=_blank` and `window.open` stay inside Orbit tabs.

### Data reliability
- Local JSON writes are atomic and create a `.bak` copy of the previous state.
- Crash/session recovery state is persisted.
- History, downloads, bookmarks and notes remain local-first.

### Android
- Version 1.11 / versionCode 111.
- Google remains the default search provider.
- WebView cache and startup behavior are tuned for faster reopen.
- Download Manager and offline games remain supported.

### Security
- No secrets are committed to the repository.
- Security workflow checks the repository automatically.
- Backend remains environment-variable driven.
- Admin/Helper access remains RBAC protected.

### Release
- Windows Actions publishes EXE, Portable EXE and Setup EXE.
- Android Actions publishes APK and AAB.
- Website keeps direct download links independent from internal analytics.

## 1.12 — Performance / Core Edition

- SQLite становится основным локальным хранилищем (`data/orbit.db`) с WAL и индексами.
- Автоматическая миграция старых JSON-данных при первом запуске.
- Добавлен `orbit_core.py` для фоновых задач и общего coordination layer.
- `Ctrl+K` превращён в Orbit Command Center.
- Добавлены команды `/new-tab`, `/settings`, `/history`, `/downloads`, `/theme`, `/clear-cache`, `/profile`, `/workspace`, `/vpn`.
- Контекстное меню вкладки: закрытие, дубликат, pin, закрытие остальных, восстановление.
- История закрытых вкладок хранит несколько элементов вместо одного.
- Восстановление сессии увеличено до 30 вкладок.
- Ускорены параметры QtWebEngine и вынесены в `PerformancePolicy`.
- Увеличены лимиты хранения истории/загрузок в SQLite с индексами.
- Android versionCode=112 / versionName=1.12.
- GitHub Actions release notes обновлены до 1.12.
