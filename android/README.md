# Orbit Browser Android 1.16.22

Это полноценный нативный Android-клиент Orbit Browser, а не просто ссылка на сайт.

Возможности:
- вкладки;
- адресная строка и Google-поиск;
- назад / вперёд / обновить;
- несколько вкладок и закрытие вкладок долгим нажатием;
- загрузка файлов через системный Download Manager;
- системное меню Orbit;
- WebView с JavaScript, cookies, Local Storage и cache;
- Orbit User-Agent;
- подключение к общей Orbit Web/API-экосистеме.

## Сборка

Откройте папку `android` в Android Studio.

JDK: 17
Android SDK: 35

APK:
Build → Build Bundle(s) / APK(s) → Build APK(s)

AAB:
Build → Generate Signed Bundle / APK → Android App Bundle

### Автосборка
GitHub Actions собирает release APK и AAB. Не нужен gradlew: CI устанавливает Gradle сам.

### Обновления Windows
Windows-клиент проверяет последний GitHub Release и предлагает скачать `OrbitBrowser-Setup.exe`. Данные `%LOCALAPPDATA%\\OrbitBrowser` не удаляются установщиком.

### Android
APK/AAB публикуются в GitHub Release. Android не может молча установить новый APK без участия пользователя; приложение может направить пользователя к релизу для установки.
