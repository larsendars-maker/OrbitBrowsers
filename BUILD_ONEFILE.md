# Orbit Browser 1.16.12 — Single-file Windows build

`build_all.bat` now builds a single Windows executable:

`gotovo\OrbitBrowser.exe`

No `_internal` folder or neighboring PyInstaller runtime files are required to launch it. Python, PySide6, requests and Chromium/Qt runtime are bundled into the executable by PyInstaller.

The first launch may take longer because one-file PyInstaller extracts its bundled runtime to a temporary directory automatically. The temporary extraction is handled by the application runtime and is not a folder the user must keep next to the EXE.

Android outputs remain:
- `gotovo\OrbitBrowser-Android.apk`
- `gotovo\OrbitBrowser-Android.aab`

The Inno Setup installer also installs the single-file `OrbitBrowser.exe`.
