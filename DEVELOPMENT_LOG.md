# Orbit Browser — Development Log v1.12

## Архитектура
- Рабочая Windows-архитектура возвращена на функциональную single-window основу с внутренними вкладками.
- Внутренние Orbit-разделы не создают отдельные окна.
- `target=_blank` / `window.open` направляются в вкладки Orbit.

## Производительность
- Убран пользовательский переключатель «сбалансированный/медленный».
- Orbit всегда использует fast configuration.
- Сетевые проверки и sync не блокируют первый показ UI.
- Chromium renderer limit зафиксирован на производительном значении.
- Web cache использует диск.

## Session recovery
- Последние вкладки сохраняются при нормальном закрытии.
- Последняя закрытая вкладка восстанавливается через Ctrl+Shift+T.
- Локальные JSON-состояния записываются атомарно с `.bak`.

## Productivity
- Ctrl+L, Ctrl+T, Ctrl+W, Ctrl+Shift+T, Ctrl+K, Ctrl+H, Ctrl+D, Ctrl+J, Alt+Left, Alt+Right.

## Security
- Пароли аккаунтов не хранятся в открытом виде.
- Demo secrets и реальные credentials не должны попадать в Git.
- `.env`, keys, certificates, cache и bytecode исключаются через `.gitignore`.

## Android
- Версия обновлена до 1.11.
- WebView cache остаётся доступным для быстрого возврата на ранее загруженные страницы.
- Параметры playback/open-window не позволяют плодить внешние окна.

## Release
- Windows и Android собираются отдельными GitHub Actions.
- Перед release рекомендуется выполнить build, smoke tests и security scan.

## Ограничения проверки
- Полный Gradle/Windows release в этой среде не запускался.
- Проверены структура проекта, Python syntax и архив.

### v1.12 Core pass

Перестроен слой локального хранения на SQLite с WAL/NORMAL и индексами. Сохранена обратная совместимость: старые JSON-файлы автоматически импортируются один раз.

Добавлен небольшой `OrbitCore` для фоновых задач и недавних команд. `Ctrl+K` теперь открывает Command Center, а omnibox понимает Orbit-команды через `/...`.

Вкладки получили контекстное меню и стек нескольких недавно закрытых вкладок. Сессионное восстановление ограничено безопасным числом активных вкладок.

Полный Windows/Android release build остаётся зоной GitHub Actions; локально выполнены syntax/smoke/storage/security проверки.
