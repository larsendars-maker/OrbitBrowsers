# GitHub Actions — Android

1. Открой GitHub → OrbitBrowsers → Actions.
2. Выбери **Build Orbit Android**.
3. Нажми **Run workflow**.
4. Дождись зелёной галочки.
5. Внизу открой **Artifacts** → `OrbitBrowser-Android-1.16.17`.

В артефакте:
- `OrbitBrowser-debug.apk` — для тестов;
- `OrbitBrowser.apk` — release APK (unsigned, если не задан signing key);
- `OrbitBrowser.aab` — AAB для публикации;
- `SHA256SUMS.txt` — контрольные суммы.

Windows специально не собирается GitHub Actions. Windows собирай локально через `build_windows.bat` или `build_exe.py`.
