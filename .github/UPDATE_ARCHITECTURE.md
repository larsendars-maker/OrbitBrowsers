# Orbit Browser — обновления

Windows:
1. Пушится тег `vX.Y.Z`.
2. GitHub Actions собирает Portable EXE и NSIS/Inno Setup EXE.
3. Release публикуется в GitHub.
4. Orbit Browser проверяет `releases/latest`.
5. Если версия новее, предлагается скачать `OrbitBrowser-Setup.exe`.

Android:
1. Тот же тег собирает APK/AAB.
2. Файлы прикладываются к GitHub Release.
3. Пользователь подтверждает установку APK сам, как требует Android.

Пользовательские данные Windows лежат в `%LOCALAPPDATA%\\OrbitBrowser` и не должны храниться в папке установки.
