Orbit Browser 1.16.12 — BUILD ALL

Запуск: build_all.bat

Собирает:
- gotovо\OrbitBrowser.exe (один EXE, PyInstaller --onefile)
- gotovо\OrbitBrowser-Setup.exe (если установлен Inno Setup)
- gotovо\OrbitBrowser-Android.apk
- gotovо\OrbitBrowser-Android.aab

Для Android нужны JDK 17+ и Android SDK. Gradle 8.7, если не найден, скачивается автоматически в .buildtools.
