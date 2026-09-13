@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "ROOT=%CD%"
set "OUT=%ROOT%\gotovo"
set "TOOLS=%ROOT%\.buildtools"
set "ANDROID=%ROOT%\android"
set "BUILD_OUT=%ROOT%\build_out"

if not exist "%OUT%" mkdir "%OUT%"
if not exist "%TOOLS%" mkdir "%TOOLS%"

echo ========================================
echo Orbit Browser - Build All
 echo ========================================
echo.

rem ---------- WINDOWS ----------
echo [1/2] Building Windows...
call "%ROOT%\build_windows.bat"
if errorlevel 1 (
  echo Windows build FAILED.
  exit /b 1
)

if not exist "%BUILD_OUT%\OrbitBrowser\OrbitBrowser.exe" (
  echo Windows EXE was not produced.
  exit /b 1
)

if exist "%OUT%\OrbitBrowser" rmdir /s /q "%OUT%\OrbitBrowser"
robocopy "%BUILD_OUT%\OrbitBrowser" "%OUT%\OrbitBrowser" /E /NFL /NDL /NJH /NJS /NC /NS >nul
if errorlevel 8 (
  echo Failed to copy Windows build.
  exit /b 1
)

echo Windows build OK: %OUT%\OrbitBrowser\OrbitBrowser.exe

rem ---------- INSTALLER ----------
echo.
echo Building Windows installer...
call "%ROOT%\build_installer.bat"
if errorlevel 1 (
  echo Installer build FAILED. Continuing with Android build.
) else (
  if exist "%ROOT%\installer\OrbitBrowser-Setup.exe" copy /y "%ROOT%\installer\OrbitBrowser-Setup.exe" "%OUT%\OrbitBrowser-Setup.exe" >nul
)

rem ---------- ANDROID ----------
echo.
echo [2/2] Building Android APK/AAB...
if not exist "%ANDROID%\build.gradle.kts" (
  echo Android project not found: %ANDROID%
  exit /b 1
)

set "GRADLE_CMD="
if exist "%ANDROID%\gradlew.bat" set "GRADLE_CMD=%ANDROID%\gradlew.bat"
if not defined GRADLE_CMD (
  where gradle >nul 2>nul
  if not errorlevel 1 set "GRADLE_CMD=gradle"
)
if not defined GRADLE_CMD if exist "%TOOLS%\gradle-8.7\bin\gradle.bat" set "GRADLE_CMD=%TOOLS%\gradle-8.7\bin\gradle.bat"

if not defined GRADLE_CMD (
  echo Gradle not found. Downloading Gradle 8.7 to %TOOLS%...
  if not exist "%TOOLS%\gradle-8.7-bin.zip" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri 'https://services.gradle.org/distributions/gradle-8.7-bin.zip' -OutFile '%TOOLS%\gradle-8.7-bin.zip'"
    if errorlevel 1 (
      echo Could not download Gradle.
      exit /b 1
    )
  )
  if not exist "%TOOLS%\gradle-8.7\bin\gradle.bat" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force '%TOOLS%\gradle-8.7-bin.zip' '%TOOLS%'"
    if errorlevel 1 (
      echo Could not extract Gradle.
      exit /b 1
    )
  )
  set "GRADLE_CMD=%TOOLS%\gradle-8.7\bin\gradle.bat"
)

if not defined JAVA_HOME (
  where java >nul 2>nul
  if errorlevel 1 (
    echo Java/JDK was not found. Install JDK 17+ or configure JAVA_HOME.
    exit /b 1
  )
)

if defined ANDROID_HOME (
  echo Android SDK: %ANDROID_HOME%
) else if defined ANDROID_SDK_ROOT (
  echo Android SDK: %ANDROID_SDK_ROOT%
) else (
  echo Android SDK environment variable is not set.
  echo Set ANDROID_HOME or ANDROID_SDK_ROOT to your Android SDK directory.
  exit /b 1
)

pushd "%ANDROID%"
call "%GRADLE_CMD%" --no-daemon clean assembleRelease bundleRelease
if errorlevel 1 (
  popd
  echo Android build FAILED.
  exit /b 1
)
popd

if exist "%ANDROID%\app\build\outputs\apk\release\app-release.apk" copy /y "%ANDROID%\app\build\outputs\apk\release\app-release.apk" "%OUT%\OrbitBrowser-Android.apk" >nul
if exist "%ANDROID%\app\build\outputs\bundle\release\app-release.aab" copy /y "%ANDROID%\app\build\outputs\bundle\release\app-release.aab" "%OUT%\OrbitBrowser-Android.aab" >nul

if not exist "%OUT%\OrbitBrowser-Android.apk" (
  echo APK was not produced.
  exit /b 1
)
if not exist "%OUT%\OrbitBrowser-Android.aab" (
  echo AAB was not produced.
  exit /b 1
)

echo.
echo ========================================
echo BUILD COMPLETE
echo ========================================
echo Windows:  %OUT%\OrbitBrowser\OrbitBrowser.exe
echo Installer: %OUT%\OrbitBrowser-Setup.exe
echo Android:  %OUT%\OrbitBrowser-Android.apk
echo Android:  %OUT%\OrbitBrowser-Android.aab
echo.
exit /b 0
