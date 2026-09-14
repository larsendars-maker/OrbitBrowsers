# Orbit Browser — обновления

Windows:
1. GitHub Actions собирает только `OrbitBrowser.exe`.
2. EXE публикуется в GitHub Release без дублей Portable/Setup.
3. Orbit Browser проверяет доступную версию в фоне и предлагает обновление.

Android:
1. GitHub Actions собирает только APK.
2. APK прикладывается к GitHub Release как `OrbitBrowser.apk`.
3. Приложение раз в 6 часов проверяет `android/VERSION.txt` и может скачать APK обновления.
4. Android всё равно требует системного подтверждения установки APK; полностью бесшумное обновление без Play Store/управляемого устройства невозможно.

Пользовательские данные Windows лежат в `%LOCALAPPDATA%\\OrbitBrowser` и не должны храниться в папке установки.
