# ORBIT BROWSER — MASTER BRIEF FOR CLAUDE

## 1. Роль

Привет, Claude!

Ты — Senior Frontend / UI/UX разработчик и архитектор приложений.
Помоги продолжить и системно переработать проект **Orbit Browser**.

Главная задача: не сделать новый мокап, а превратить существующий проект в цельную, быструю, безопасную и расширяемую экосистему.

Три платформы:

1. Windows Desktop Browser
2. Android Browser
3. Website / Landing

Все три должны выглядеть и ощущаться как один продукт Orbit.

Не переписывай рабочую функциональность без причины.
Сначала изучи существующий код, сохрани полезное, удали дубли и мёртвый код, затем рефактори.

---

# 2. Что такое Orbit

**Orbit Browser** — браузер нового поколения с космической эстетикой, собственной поисковой системой Orbit, профилями, синхронизацией, темами, заметками, загрузками, историей, офлайн-инструментами и общей экосистемой между Windows и Android.

Основные слоганы:

> Быстрый. Удобный. Твой.

> Быстрее. Удобнее. Ближе к тебе.

Orbit не должен выглядеть как стандартный Electron/WebView-шаблон.

---

# 3. Текущий источник UI

В проекте есть исходный монолитный `orbit.html`.

Он уже содержит:

- адаптивный desktop/mobile layout;
- sidebar;
- mobile bottom navigation;
- drawer;
- Home;
- Tabs;
- Bookmarks;
- History;
- Downloads;
- Passwords;
- Extensions;
- Notes;
- Orbit AI;
- Admin;
- Settings;
- glassmorphism;
- космический background;
- переключение views через JavaScript.

Текущий HTML использует Tailwind CDN и Google Fonts Inter, а логика находится прямо в одном HTML-файле.

Важно: этот файл считать **визуальным источником правды**, но не конечной архитектурой.

Код нужно разбить на нормальные компоненты.

---

# 4. Важные проблемы исходного HTML, которые нужно исправить

## 4.1 Монолит

Сейчас UI, state и логика смешаны в одном HTML:

- navigation;
- view rendering;
- данные;
- actions;
- password logic;
- drawer;
- admin data.

Нужно разделить их на компоненты и состояние.

## 4.2 Жёстко зашитый пользователь

В текущем HTML напрямую указан пользователь:

- Larsenda
- роль Администратор
- email и другие демонстрационные данные.

Это должно приходить из auth/profile state.

## 4.3 Критическая проблема с паролем

В исходном HTML демонстрационный пароль фактически зашит в JavaScript и раскрывается функцией `togglePass()`.

Так делать нельзя.

Никогда не хранить:

- реальные пароли;
- access tokens;
- refresh tokens;
- DB credentials;
- API keys

в HTML/JS/репозитории.

Все демонстрационные секреты удалить из production-кода.

## 4.4 Админ-панель

В исходном HTML Admin Panel отображается как часть UI без реальной RBAC-проверки.

Нужно:

- скрывать Admin Panel для обычного пользователя;
- разрешать нужные действия только `admin`;
- `helper` должен получать только разрешённые moderation/support функции;
- backend тоже обязан проверять роль;
- нельзя полагаться только на frontend.

## 4.5 AI / внешние сервисы

В HTML есть ссылки:

- Gemini
- ChatGPT
- Claude
- Perplexity

Это нормальные ссылки.

Но Orbit не должен передавать пользовательский контекст во внешний AI без явного действия пользователя.

---

# 5. Design System

## Цвета

Основной фон:

- `#0A0A1A`
- `#0F0F1A`
- `#2A1B5E`

Акценты:

- Purple `#8B5CF6`
- Cyan `#22D3EE`
- Blue `#3B82F6`

Допустимы градиенты:

`purple → blue → cyan`

## Glassmorphism

Базовая идея:

```css
background: rgba(255,255,255,0.03);
backdrop-filter: blur(12px);
border: 1px solid rgba(255,255,255,0.06);
```

Hover должен усиливать:

- background;
- border;
- glow.

## Typography

Inter.

## Shape

- rounded-lg;
- rounded-xl;
- rounded-2xl;
- аккуратные панели;
- тонкие разделители.

## Motion

Анимации должны быть:

- плавными;
- короткими;
- ненавязчивыми;
- с уважением к `prefers-reduced-motion`.

Не использовать анимации, которые задерживают запуск приложения.

---

# 6. Windows Browser

## Layout

Desktop:

- sidebar слева;
- toolbar/address bar сверху;
- tabs в browser chrome;
- основная web area справа.

Важно:

**не создавать отдельное приложение/окно для каждой функции.**

Все внутренние страницы Orbit:

- Settings;
- Profile;
- History;
- Downloads;
- Notes;
- Bookmarks;
- Studio;
- Dashboard

открываются внутри Orbit.

`target="_blank"` должен становиться новой вкладкой Orbit, а не внешним окном.

---

# 7. Sidebar

Разделы:

- Главная
- Закладки
- История
- Загрузки
- Заметки
- Профиль
- Настройки
- Orbit Studio
- Workspaces
- Spaces
- VPN

Внизу:

Profile Card:

- avatar;
- name;
- role;
- level;
- online/offline.

На мобильном используются:

- bottom navigation;
- drawer.

---

# 8. Главная

Главный экран:

- Orbit logo;
- приветствие;
- поиск;
- Quick Sites;
- статистика;
- новости.

Search:

> Поиск в Orbit...

По умолчанию поисковая система:

**ORBIT**

Не ставить Google/Bing/DuckDuckGo как default.

---

# 9. Orbit Search

Нужна единая abstraction:

```text
SearchProvider
```

Default:

```text
orbit
```

Настройки пользователя могут менять search provider только если это предусмотрено системой.

Если Orbit Search недоступен:

- не открывать внешний браузер;
- показать внутренний Orbit error state;
- предоставить fallback только как явную опцию пользователя.

---

# 10. Tabs

В браузере вкладки должны существовать, но:

**не показывать отдельный раздел "Вкладки" в sidebar**, если он не нужен пользователю.

Сами вкладки:

- сверху;
- draggable;
- close;
- pin;
- duplicate;
- restore;
- tab groups.

Мобильный интерфейс — без desktop tab strip.

---

# 11. Bookmarks

Поддержать:

- create;
- edit;
- delete;
- folders;
- search;
- pin;
- reorder;
- sync.

---

# 12. History

Каждая запись:

```text
favicon
title
url
timestamp
```

Функции:

- search;
- filter;
- delete;
- clear all;
- clear by period;
- open.

Не хранить историю только в DOM.
Использовать локальное persistent storage.

---

# 13. Downloads

Каждая загрузка:

```text
file name
size
downloaded
status
progress
speed
created_at
```

Статусы:

- downloading
- paused
- completed
- failed
- cancelled

Действия:

- pause;
- resume;
- retry;
- open;
- show in folder;
- remove.

Android:
использовать системный Download Manager.

Windows:
использовать Chromium/Electron download events.

---

# 14. Notes

Notes должны быть настоящими данными.

Функции:

- create;
- edit;
- delete;
- pin;
- search;
- folders;
- attach current page;
- sync.

UI может использовать колонки:

- Plans;
- Ideas;
- Personal.

Но пользователь должен иметь возможность создавать собственные.

---

# 15. Profile

Profile:

- avatar;
- name;
- role;
- level;
- EXP;
- achievements;
- titles.

Пример:

```text
Level 12
1,250 / 2,000 EXP
```

Titles должны иметь состояния:

```text
✓ Получен
○ Недоступен
• Надет
```

После синхронизации одинаковое состояние на Windows и Android.

---

# 16. Roles / RBAC

Минимальные роли:

- admin;
- helper;
- user.

Frontend:

- скрывать запрещённые UI.

Backend:

- обязательно проверять authorization.

User:

- не видит Admin Panel.

Helper:

- видит только разрешённые support/moderation функции.

Admin:

- полный административный доступ.

---

# 17. Admin Panel

Секции:

- users;
- devices;
- profiles;
- sessions;
- downloads;
- audit logs;
- server health;
- feature flags;
- releases;
- maintenance.

Статистика:

- Users;
- Online;
- Downloads;
- Sessions.

Не использовать фейковые цифры.

Все значения берутся из API.

---

# 18. Orbit AI

Orbit AI — отдельный модуль.

Не отправлять данные пользователя внешнему AI без явного действия.

Внешние ссылки:

- Gemini;
- ChatGPT;
- Claude;
- Perplexity.

Если открытие ссылки необходимо:

в Windows — новая вкладка Orbit;
в Android — новая вкладка Orbit / соответствующий внутренний browser flow.

---

# 19. Themes / Orbit Studio

Темы:

- VOID
- ICE
- BLUE
- PURPLE
- CYBER
- SUNSET
- EMERALD
- RED

Theme state должен реально применяться и сохраняться без перезапуска.

Orbit Studio:

- accent;
- background;
- gradient;
- blur;
- glow;
- radius;
- density;
- scale;
- tabs;
- address bar;
- sidebar;
- animations.

Functions:

- Create Theme;
- Save;
- Import;
- Export;
- Reset.

---

# 20. Android

Android — полноценное приложение, а не сайт в WebView.

Стек:

- Kotlin;
- Android SDK;
- native UI.

Mobile:

- splash;
- Orbit branding;
- browser;
- bottom navigation;
- profile;
- history;
- bookmarks;
- downloads;
- notes;
- settings;
- themes;
- sync.

Нижняя навигация:

```text
Главная
Закладки
История
Загрузки
Профиль
```

Дополнительные функции открываются через drawer/profile/settings.

---

# 21. Offline Mode

Если интернета нет:

не показывать бесполезную пустую страницу.

Показывать:

```text
ORBIT OFFLINE
```

Игры:

- Snake;
- Block Blast.

Игры полностью локальные.

Offline mode не должен ломать:

- history;
- downloads list;
- bookmarks;
- notes.

---

# 22. Website

Сайт — landing/documentation/download portal Orbit.

Hero:

- Orbit logo;
- title;
- short description;
- Windows download;
- Android download.

Обязательно сделать ДВА независимых download cards:

## Windows

```text
OrbitBrowser-Setup.exe
Прямая загрузка
GitHub Release
```

## Android

```text
OrbitBrowser.apk
Прямая загрузка
GitHub Release
```

Прямая ссылка должна вести непосредственно на файл release.

Не зависеть от внутренней таблицы Downloads для выдачи файла.

---

# 23. Changelog

Текущая публичная версия:

```text
1.0
```

Дальше план:

```text
1.1
1.2
1.3
...
2.0
```

Каждая запись:

- version;
- date;
- title;
- changes;
- platform.

---

# 24. Frontend architecture

Рекомендуемый стек:

- React;
- TypeScript;
- Tailwind CSS;
- Framer Motion;
- Vite;
- React Router.

State:

- Zustand предпочтительно для умеренной сложности;
- Redux Toolkit допустим, если state станет значительно сложнее.

Структура:

```text
src/
├── app/
│   ├── router/
│   ├── providers/
│   └── store/
├── components/
│   ├── layout/
│   ├── browser/
│   ├── profile/
│   ├── bookmarks/
│   ├── history/
│   ├── downloads/
│   ├── notes/
│   ├── settings/
│   ├── admin/
│   └── ai/
├── features/
│   ├── auth/
│   ├── sync/
│   ├── search/
│   ├── themes/
│   ├── downloads/
│   └── history/
├── pages/
├── services/
├── hooks/
├── utils/
├── types/
├── styles/
└── assets/
```

---

# 25. Backend

Предпочтительный стек:

- Node.js;
- Express;
- TypeScript;
- Prisma;
- PostgreSQL.

FastAPI допустим, если существующий backend уже написан на Python и его дорого/опасно переписывать.

---

# 26. Database

Основная БД:

**PostgreSQL**

Не MongoDB по умолчанию, если нет архитектурной причины.

Основные таблицы:

```text
users
sessions
profiles
devices
bookmarks
history
downloads
notes
themes
workspaces
spaces
titles
achievements
user_titles
extensions
audit_logs
sync_state
feature_flags
```

---

# 27. Users

```text
users
-----
id
email
username
password_hash
role
status
created_at
updated_at
last_login_at
```

Не хранить обычный пароль.

---

# 28. Passwords

Критически важно:

Пароли для входа:

**ХЕШИРОВАТЬ**, а не шифровать.

Использовать:

- Argon2id предпочтительно;
- bcrypt допустим.

Нельзя:

```text
password = plain text
password = AES encrypted
```

Для browser password manager:

если нужна синхронизация, используйте client-side encryption / zero-knowledge подход.

Master key не хранить на сервере в открытом виде.

---

# 29. Password Vault

Таблица может содержать:

```text
id
user_id
site
login
encrypted_payload
created_at
updated_at
```

`encrypted_payload` шифруется на клиенте.

Сервер не должен видеть plaintext password.

---

# 30. Sessions

```text
sessions
--------
id
user_id
device_id
refresh_token_hash
created_at
expires_at
revoked_at
last_seen_at
```

Refresh tokens хранить в защищённом виде.

---

# 31. Authentication

Рекомендуемый flow:

```text
Login
 ↓
short-lived access token
 ↓
refresh token
 ↓
rotation
 ↓
revocation
```

Не хранить JWT в localStorage, если можно использовать более безопасный механизм.

Для web app предпочтительно:

- HttpOnly;
- Secure;
- SameSite cookies.

CSRF protection обязателен для cookie-based auth.

---

# 32. API

Пример:

```text
/api/auth/register
/api/auth/login
/api/auth/refresh
/api/auth/logout
/api/auth/me

/api/users
/api/users/:id

/api/profiles
/api/profiles/:id

/api/bookmarks
/api/history
/api/downloads
/api/notes
/api/themes
/api/workspaces
/api/spaces
/api/titles
/api/achievements

/api/sync/state
/api/sync/pull
/api/sync/push

/api/search
/api/site/stats
/api/releases
/api/features

/api/admin/users
/api/admin/sessions
/api/admin/logs
/api/admin/health
```

---

# 33. Audit Log

Логировать:

- login;
- logout;
- registration;
- download;
- bookmark changes;
- settings changes;
- profile changes;
- admin actions.

НЕ логировать IP.

Минимальная таблица:

```text
audit_logs
----------
id
user_id
action
entity
entity_id
metadata
created_at
```

`metadata` не должен содержать:

- password;
- token;
- secret;
- private key.

---

# 34. Privacy

Главный принцип:

**Без IP-логирования.**

Не собирать лишнюю телеметрию.

Если analytics нужен:

- анонимизированные counters;
- opt-in/clear disclosure;
- никаких паролей или содержимого страниц.

---

# 35. Sync

Синхронизировать:

- profile;
- bookmarks;
- history;
- notes;
- themes;
- workspaces;
- spaces;
- titles;
- achievements;
- settings.

Синхронизация:

- background;
- debounce;
- retry;
- versioning;
- conflict resolution.

WebSocket / Socket.io можно использовать для realtime signals.

Не гонять полноценное состояние каждую секунду.

---

# 36. Render

Production backend разворачивается на **Render**.

Рекомендуемая схема:

```text
Render
├── Web Service: orbit-api
├── PostgreSQL: orbit-db
├── optional Worker: orbit-worker
└── optional Redis / Key Value
```

Основные environment variables:

```text
DATABASE_URL
JWT_SECRET
REFRESH_TOKEN_SECRET
ENCRYPTION_KEY
CORS_ORIGINS
APP_ENV
GEMINI_API_KEY (только если реально используется backend)
```

Секреты не хранить в Git.

Не писать реальные значения в:

- `.env.example`;
- README;
- source code.

`.env.example` должен содержать только названия переменных и безопасные placeholder values.

---

# 37. Render Health

Добавить:

```text
GET /health
```

Ответ:

```json
{
  "ok": true,
  "service": "orbit-api",
  "version": "1.0"
}
```

Также желательно:

```text
/health/db
/health/cache
/health/sync
```

---

# 38. CORS

Разрешать только реальные production origins.

Не использовать:

```text
Access-Control-Allow-Origin: *
```

в production вместе с credentials.

---

# 39. Performance

Главный приоритет:

**очень быстрый запуск.**

Правила:

- UI показывается сразу;
- network не блокирует старт;
- initial render минимален;
- lazy-load тяжёлых страниц;
- background sync;
- debounce;
- caching;
- не создавать лишние windows;
- не держать лишние processes;
- не выполнять тяжёлые операции на UI thread;
- не загружать AI/analytics заранее;
- не рендерить скрытые страницы.

Для website:

- code splitting;
- asset compression;
- lazy images;
- prefetch только нужного.

---

# 40. Mobile performance

Android не должен долго ждать API перед показом UI.

Flow:

```text
Launch
 ↓
Splash / WELCOM
 ↓
Local state
 ↓
Main UI
 ↓
background sync
```

Если сеть медленная, пользователь всё равно видит Orbit.

---

# 41. Browser speed

Не открывать новый процесс для каждой Orbit feature.

Внутренние страницы:

```text
orbit://home
orbit://settings
orbit://history
orbit://downloads
orbit://profile
orbit://notes
orbit://studio
```

не должны запускать отдельный браузер.

---

# 42. Security cleanup

Перед каждым release:

Удалить:

```text
.env
.env.local
*.pem
*.key
credentials.*
secrets.*
*.pyc
__pycache__
node_modules
dist
build
tmp
logs with secrets
```

Проверить Git:

```text
git ls-files
```

и scanner.

Секреты должны находиться только в:

- GitHub Secrets;
- Render Environment.

---

# 43. GitHub Actions

Нужны только необходимые workflows.

## Windows

```text
.github/workflows/build-windows.yml
```

Процесс:

checkout
→ setup Node
→ npm ci
→ tests
→ build
→ electron-builder
→ Portable
→ Setup
→ upload artifacts
→ optional GitHub Release

## Android

```text
.github/workflows/build-android.yml
```

Процесс:

checkout
→ JDK 17
→ Android SDK
→ Gradle
→ tests
→ APK
→ AAB
→ upload
→ Android Release

Не оставлять старые/дублирующие workflows.

---

# 44. Releases

Windows release:

```text
tag: Windows
```

Assets:

```text
OrbitBrowser-Setup.exe
OrbitBrowser-Portable.exe
```

Android release:

```text
tag: Android
```

Assets:

```text
OrbitBrowser.apk
OrbitBrowser.aab
```

Website download buttons должны ссылаться непосредственно на эти assets.

---

# 45. Changelog roadmap

Public version:

```text
1.0
```

Next:

```text
1.1
1.2
1.3
...
2.0
```

Не писать будущую функцию как уже реализованную.

Разделять:

- Released;
- Planned;
- Experimental.

---

# 46. Titles / Achievements

Добавить отдельную систему:

```text
titles
achievements
user_titles
user_achievements
```

Пример:

```text
Orbit Pioneer
Early User
Power User
Sync Master
Customizer
Explorer
```

В UI:

```text
Получен
Недоступен
Надет
```

Синхронизировать между устройствами.

---

# 47. Website UX

Главная:

Hero
→ Why Orbit
→ Platforms
→ Features
→ Offline Mode
→ Themes
→ Changelog
→ Downloads
→ GitHub
→ Footer

Windows и Android download cards должны быть отдельными.

Не писать "скачать сайт".

Пользователь должен понимать:

- это Windows приложение;
- это Android приложение;
- это сайт Orbit.

---

# 48. What to do first

НЕ начинай с переписывания всего.

Сначала:

1. Audit.
2. Создай `PROJECT_AUDIT.md`.
3. Зафиксируй текущую структуру.
4. Выдели рабочий код.
5. Исправь security issues.
6. Разбей `orbit.html` на компоненты.
7. Создай common design system.
8. Подключи real state.
9. Потом API.
10. Потом PostgreSQL.
11. Потом auth/RBAC.
12. Потом sync.
13. Потом GitHub Actions.
14. Потом release testing.

---

# 49. Definition of Done

Функция готова только если она:

- работает;
- подключена к реальным данным;
- не является мокапом;
- не ломает другие функции;
- имеет error handling;
- имеет loading state;
- имеет empty state;
- имеет mobile state;
- не создаёт лишние окна;
- не требует ручного reload.

---

# 50. Very important

Не говори, что функция готова, если она только нарисована.

Не создавай fake numbers.

Не создавай fake users.

Не создавай fake downloads.

Не создавай fake admin data.

Не оставляй demo password.

Не оставляй секреты в исходниках.

Не отправляй пользователя во внешний браузер без необходимости.

Не заменяй Android приложение сайтом/WebView только для того, чтобы быстрее закончить.

---

# 51. Текущий исходный HTML

Источник:

`orbit.html`

В текущем файле уже есть desktop sidebar, mobile bottom navigation, drawer, Home, tabs, bookmarks, history, downloads, passwords, extensions, notes, Orbit AI, admin и settings. Адаптивность сейчас переключается через media query около 768px. 

Текущий HTML подтверждает, что:
- desktop sidebar существует;
- mobile navigation существует;
- внутренние views переключаются через JavaScript;
- Home содержит search, quick access и weather;
- Downloads/History/Bookmarks/Notes/Passwords/Admin/Settings уже имеют визуальные макеты;
- Orbit AI содержит внешние ссылки на Gemini, ChatGPT, Claude и Perplexity.

При рефакторинге всё это использовать как исходную UI-модель, но перевести в React/TypeScript архитектуру.

---

# 52. Итоговая цель

Orbit должен стать одной системой:

```text
                ORBIT
                  |
      +-----------+-----------+
      |           |           |
   Windows     Android      Website
      |           |           |
      +-----------+-----------+
                  |
              Account
                  |
              Profiles
                  |
                Sync
                  |
      +-----------+-----------+
      |           |           |
   History   Bookmarks     Notes
      |           |           |
 Downloads      Themes      Titles
                  |
               Backend
                  |
               Render
                  |
             PostgreSQL
```

Главная цель:

**быстрый, красивый, безопасный, цельный и реально рабочий Orbit Browser.**
