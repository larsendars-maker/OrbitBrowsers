# Orbit Browser 1.16.17 — сборка

## Windows

На Windows запусти `build_windows.bat` для Portable EXE или `build_all.bat` для EXE + Android (если установлен JDK/Android SDK).

## Android через GitHub

Загрузи репозиторий и открой Actions → Build Orbit Android → Run workflow.
Артефакты: debug APK, release APK, AAB и SHA256SUMS.txt.

Android использует AndroidX через `android/gradle.properties`.
