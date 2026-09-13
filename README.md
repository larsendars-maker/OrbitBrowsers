# Orbit Browser 1.15.0

Google, Bing and DuckDuckGo are opened directly in Chromium with normal search URLs. Orbit does not scrape result pages or attempt to bypass CAPTCHA/anti-bot systems; the providers see a normal browser session.

Search provider URLs:
- Google: https://www.google.com/search?q=...
- Bing: https://www.bing.com/search?q=...
- DuckDuckGo: https://duckduckgo.com/?q=...

The Orbit site is served from the FastAPI service and `/admin` is protected by the Admin role. Public responses do not expose email addresses or database details. Secrets are Render environment variables only.

Roles: User, Helper, Admin.
Titles are a separate system and are unlocked by achievements or roles. Users cannot type arbitrary titles into their profile.

To bootstrap Larsenda as Admin without storing a password in Git, set these Render secrets:
- `ORBIT_FOUNDER_EMAIL`
- `ORBIT_FOUNDER_PASSWORD`

Android source is in `android/`; GitHub Actions builds both APK and AAB.

## Orbit AI / Gemini

Set `GEMINI_API_KEY` in Render Environment Variables. The desktop client talks only to `/api/ai/*`; the Gemini key is never bundled into the EXE or sent to the client. The AI panel supports model selection, multi-turn chats, up to 4 image attachments per message, and a New Chat action.

## Orbit Support

В приложении добавлена страница `Orbit Помощь`.

- любой пользователь может создать обращение;
- после отправки действует антиспам-кд 30 секунд;
- Helper и Admin видят очередь обращений;
- Helper/Admin могут ответить и поставить статус `open`, `pending` или `closed`;
- ответы и история обращений сохраняются в PostgreSQL.

Для защиты от спама AI-запросы тоже ограничены серверным кд 5 секунд на пользователя.

## Как включить Gemini

1. Открой Render → Web Service Orbit API → Environment.
2. Добавь `GEMINI_API_KEY`.
3. Deploy.
4. В Orbit открой `Orbit AI`.
5. Выбери доступную модель.
6. Можно написать вопрос, прикрепить до четырёх фотографий или использовать быстрые действия `Разобрать фото`, `Перевести`, `Решить задачу`, `Объяснить`.

API-ключ не помещается в `orbit_browser.py`, EXE, APK или AAB. Клиент обращается к Orbit API, а сервер уже обращается к Gemini.

Модели в `server/app.py` — это список, который показывает клиенту Orbit. Если Google для твоего API-аккаунта использует другие доступные model IDs, поменяй этот список на поддерживаемые твоим аккаунтом значения.

## ПК

Для разработки Windows:

`py -3.13 -m pip install PySide6 requests`

`py -3.13 orbit_browser.py`

Для EXE:

`build_windows.bat`

Для установщика:

`build_installer.bat`

Готовый installer ожидается как `OrbitBrowser-Setup.exe`.

## Android

Android-клиент находится в `android/`. Сейчас это лёгкий клиент Orbit, который открывает Orbit Web и использует ту же серверную экосистему аккаунтов.

Для APK/AAB локально нужен Android Studio + JDK + Android SDK. В GitHub Actions workflow уже есть автоматическая сборка APK и AAB.

Главная схема:

`Windows EXE / Android APK / AAB -> Orbit API on Render -> PostgreSQL + Gemini API`

Так один аккаунт может использоваться с ПК и телефона, а секреты остаются только на сервере.

## Orbit Download Site

Официальный сайт раздачи Orbit Browser теперь встроен в FastAPI.

Настройка Render:
- `ORBIT_DOWNLOAD_URL` — прямая ссылка на файл, который должен скачиваться кнопкой.
- `ORBIT_DOWNLOAD_VERSION` — отображаемая версия.
- `ORBIT_DOWNLOAD_FILE_NAME` — имя файла, например `OrbitBrowser-Setup.exe`.
- `ORBIT_ANALYTICS_SECRET` — длинный случайный секрет для анонимного visitor ID.

Страница `/` показывает карточку скачивания и статистику.
`/admin` показывает статистику только пользователю с ролью Admin.

Статистика:
- просмотры — каждое открытие главной страницы;
- уникальные посетители — один анонимный идентификатор браузера считается один раз;
- скачивания — каждый переход по кнопке скачивания;
- уникальные скачавшие — один и тот же идентификатор считается один раз.

Сырые IP-адреса в аналитической таблице не сохраняются. Если пользователь удалил cookies, использовал другой браузер/устройство или блокирует cookies, он технически может быть посчитан как новый уникальный посетитель.


## v1.15.0 — вкладки, поддержка и Orbit AI
- Добавлена видимая кнопка закрытия `×` у каждой вкладки и `Ctrl+W`.
- Orbit AI теперь просто открывает официальный Gemini Web Chat (`https://gemini.google.com/app`), без встроенного API-чата.
- Orbit Support синхронизируется каждые 3 секунды без перезапуска.
- Пользователь видит только свои обращения. Helper/Admin видят очередь помощи.
- Ответ Helper/Admin автоматически появляется у автора после синхронизации.

## v1.15.0 — стабильность, вкладки, история, загрузки, титулы и Orbit Connect

Исправлены QWebEngine API-вызовы для истории и загрузок: Orbit теперь ведёт собственную локальную историю и журнал загрузок. Вкладки отображаются даже на главной, ужимаются при большом количестве, имеют отдельное закрытие и `Ctrl+W`.

Достижения помещены в прокручиваемую область профиля и не вылезают за карточки. Титул можно выбрать только из уже открытых; администратор может выдать титул через админ-панель.

Orbit Connect позволяет указать пользовательский HTTP/HTTPS/SOCKS5 прокси. Это не встроенный обход CAPTCHA или ограничений конкретных сервисов: Orbit просто использует указанный вами прокси после перезапуска приложения.


## v1.16.1 additions
- `build_all.bat` builds Windows EXE/installer and Android APK/AAB into `gotovo\`.
- History has open/delete/clear actions.
- Downloads have open folder, rename, delete record and VirusTotal entry.
- Disk cache/persistent web profile enabled for faster repeated page loads.
- Optional VPN requirement guard in Settings. It is not a VPN itself.
- Default search engine is Google when unset/invalid.
- Admin panel is visible only to Helper/Admin in the desktop UI; sensitive admin API routes remain server-protected.


Build v1.16.1: Windows uses PyInstaller onedir (small OrbitBrowser.exe + companion folder), and build_all.bat collects Windows/Android outputs into .\gotovo. The top bar now has a sidebar hide/show button; Android includes the same control.


## v1.16.9 — профиль, титулы, админ-панель и автообновление

- Титул применяется сразу после выбора/сохранения и сохраняется локально и на сервере.
- Админ-панель теперь видит только роль `Admin`. `Helper` работает через раздел «Помощь».
- `Larsenda` получает роль Admin на сервере при настройке `ORBIT_FOUNDER_EMAIL` (и, для автоматического создания аккаунта, `ORBIT_FOUNDER_PASSWORD`).
- Автообновление проверяет GitHub Releases каждые 30 минут после запуска, а первая проверка выполняется через 2.5 секунды. При наличии более новой версии с ассетом `OrbitBrowser-Setup.exe` Orbit показывает подтверждение, скачивает установщик с прогрессом и запускает его.
- Выбранный файл в «Загрузках» теперь подсвечивается без рамки/обводки.


## GitHub security

This repository intentionally contains no production secrets. Put `DATABASE_URL`, `GEMINI_API_KEY`, founder credentials, analytics secrets and download URLs into Render Environment Variables or GitHub Secrets. Never commit `.env`, private keys, access tokens, session exports, or production credential files.

Before pushing, run `py -3.13 tools/scan_secrets.py`.


## Регистрация необязательна
Orbit Browser запускается как гость без регистрации. Без аккаунта доступны обычный браузинг, вкладки и локальные функции. Вход открывает облачные возможности: профиль, синхронизацию, достижения и титулы, обращения, серверные настройки и админ-функции по роли.

## Сайт и релизы
Официальный сайт может вести пользователя напрямую на GitHub Releases. Задайте `ORBIT_RELEASE_URL` в Render. На сайте также размещено описание Orbit Browser и отметка, что проект создавался при участии ИИ.


## Admin shortcut
The Admin tab/link is hidden from the public website navigation and desktop sidebar. Admins can open it with `Ctrl+Shift+A`. Server-side role checks remain enabled.
