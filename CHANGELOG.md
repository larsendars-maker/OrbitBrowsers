# Orbit Browser Changelog

## 2.0 — Orbit Core Release

### Платформа
- Единая версия 2.0 для Windows, Android, backend и сайта.
- Windows release готовит EXE, Portable EXE и Setup.
- Android release готовит APK и AAB.
- Сайт показывает 2.0 и использует прямые ссылки на загрузки.

### Performance / Core
- Быстрый запуск UI без ожидания фоновых операций.
- Фоновая синхронизация, обновления и сетевые проверки.
- SQLite/WAL и индексы для локальных данных.
- Восстановление сессии и закрытых вкладок.
- Command Center через Ctrl+K.

### Tabs / Browser UX
- Перетаскивание вкладок, pin, duplicate и закрытие остальных.
- Ctrl+L, Ctrl+T, Ctrl+W, Ctrl+Shift+T, Ctrl+H, Ctrl+D, Ctrl+J, Ctrl+K.
- Внутренние страницы Orbit работают в одном окне.

### Orbit Games 2.0
- Snake сохранён как отдельная игра со своими настройками.
- Block Blast получил отдельные настройки и исправленное drag-and-drop фигур.
- Настройки Snake (темп/режим) больше не влияют на Block Blast.
- Перетаскивание Block Blast работает мышью и касанием через pointer events.
- Новая фигура появляется после успешного размещения.

### Android
- versionName=2.0.
- versionCode=200.
- Offline games обновлены до 2.0.

### Backend
- API version=2.0.

## 1.12 — Performance / Core Edition

- SQLite становится основным локальным хранилищем (`data/orbit.db`) с WAL и индексами.
- Автоматическая миграция старых JSON-данных.
- `Ctrl+K` — Orbit Command Center.
- Расширенное восстановление закрытых вкладок.
- Контекстное меню вкладок и pin.

## 1.11 — Final Polish

- Производительность и быстрый запуск.
- Single-window UX.
- Восстановление сессии.
- Security workflow.
- Windows + Android CI/CD.
