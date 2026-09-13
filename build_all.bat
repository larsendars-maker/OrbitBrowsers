@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "ROOT=%~dp0"
set "OUT=%ROOT%gotovo"
set "PC=%OUT%\OrbitBrowser"
set "TOOLS=%ROOT%\.buildtools"
set "ANDROID=%ROOT%\android"

if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%PC%" >nul 2>&1
mkdir "%TOOLS%" >nul 2>&1

echo ============================================
echo ORBIT BUILD ALL
 echo ============================================

echo [1/5] Installing PC build dependencies...
py -3.13 -m pip install --upgrade pip
if errorlevel 1 goto :fail
py -3.13 -m pip install PySide6 requests pyinstaller
if errorlevel 1 goto :fail

echo [2/5] Building Windows OrbitBrowser folder...
py -3.13 build_exe.py
if errorlevel 1 goto :fail
if not exist "%ROOT%build_out\OrbitBrowser\OrbitBrowser.exe" goto :fail
xcopy /e /i /y "%ROOT%build_out\OrbitBrowser" "%PC%" >nul

echo [3/5] Building Windows installer...
call build_installer.bat
if errorlevel 1 echo WARNING: Installer build skipped/failed. The portable folder is still ready.
if exist "%ROOT%installer\OrbitBrowser-Setup.exe" copy /y "%ROOT%installer\OrbitBrowser-Setup.exe" "%OUT%\OrbitBrowser-Setup.exe" >nul

echo [4/5] Building Android APK/AAB...
call :android_build
if errorlevel 1 echo WARNING: Android build could not be completed on this PC.

echo [5/5] Final output:
echo.
dir /b "%OUT%"
echo.
echo PC portable build: %PC%
echo Windows EXE: %PC%\OrbitBrowser.exe
echo Android outputs are copied to %OUT% when the Android SDK/Java are available.
echo ============================================
echo DONE
echo ============================================
exit /b 0

:android_build
pushd "%ANDROID%"
set "GRADLE_CMD="
if exist "gradlew.bat" set "GRADLE_CMD=gradlew.bat"
if not defined GRADLE_CMD where gradle >nul 2>nul && set "GRADLE_CMD=gradle"
if not defined GRADLE_CMD (
  echo Gradle wrapper/Gradle not found.
  echo Install Android Studio or Gradle, then run this file again.
  popd
  exit /b 1
)
call %GRADLE_CMD% assembleRelease bundleRelease
if errorlevel 1 (
  popd
  exit /b 1
)
if exist "app\build\outputs\apk\release\app-release.apk" copy /y "app\build\outputs\apk\release\app-release.apk" "%OUT%\OrbitBrowser-Android.apk" >nul
if exist "app\build\outputs\bundle\release\app-release.aab" copy /y "app\build\outputs\bundle\release\app-release.aab" "%OUT%\OrbitBrowser-Android.aab" >nul
popd
exit /b 0

:fail
cd /d "%ROOT%"
echo BUILD FAILED.
exit /b 1
