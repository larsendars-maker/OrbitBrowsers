@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "ROOT=%~dp0"
set "OUT=%ROOT%gotovo"
set "TOOLS=%ROOT%.buildtools"
set "ANDROID_DIR=%ROOT%android"
set "WIN_BUILD=%ROOT%build_out"
set "WIN_EXE=%WIN_BUILD%\OrbitBrowser.exe"
set "GRADLE_HOME=%TOOLS%\gradle-8.7"
set "GRADLE_ZIP=%TOOLS%\gradle-8.7-bin.zip"
set "GRADLE_CMD="
set "FAILED=0"

if "%ROOT:~-1%"=="\\" set "ROOT=%ROOT:~0,-1%"

set "LOG=%OUT%\build.log"
if not exist "%OUT%" mkdir "%OUT%"
if not exist "%TOOLS%" mkdir "%TOOLS%"

echo ========================================================
echo              ORBIT BROWSER - BUILD ALL 1.16.17
echo ========================================================
echo ROOT: %ROOT%
echo OUT : %OUT%
echo.

echo [1/2] Windows single-file EXE
echo.

py -3.13 -c "import sys; print(sys.version)"
if errorlevel 1 (
    echo [ERROR] Python 3.13 is not available through the py launcher.
    set "FAILED=1"
) else (
    py -3.13 -m pip install --upgrade pip PySide6 requests pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install Python build dependencies.
        set "FAILED=1"
    ) else (
        if exist "%WIN_BUILD%" rmdir /s /q "%WIN_BUILD%"
        if exist "%ROOT%build_work" rmdir /s /q "%ROOT%build_work"
        if exist "%ROOT%build_spec" rmdir /s /q "%ROOT%build_spec"

        py -3.13 "%ROOT%\build_exe.py"
        if errorlevel 1 (
            echo [ERROR] PyInstaller build failed.
            set "FAILED=1"
        ) else if not exist "%WIN_EXE%" (
            echo [ERROR] OrbitBrowser.exe was not produced at:
            echo         %WIN_EXE%
            set "FAILED=1"
        ) else (
            if exist "%OUT%\OrbitBrowser.exe" del /q "%OUT%\OrbitBrowser.exe"
            copy /Y "%WIN_EXE%" "%OUT%\OrbitBrowser.exe" >nul
            if errorlevel 1 (
                echo [ERROR] Could not copy OrbitBrowser.exe to output folder.
                set "FAILED=1"
            ) else (
                echo [OK] Windows: %OUT%\OrbitBrowser.exe
            )
        )
    )
)

if exist "%ROOT%OrbitBrowser.iss" (
    where ISCC.exe >nul 2>&1
    if not errorlevel 1 (
        echo.
        echo [INFO] Building Windows installer...
        if exist "%ROOT%installer" rmdir /s /q "%ROOT%installer"
        mkdir "%ROOT%installer" >nul 2>&1
        ISCC.exe "%ROOT%\OrbitBrowser.iss"
        if errorlevel 1 (
            echo [WARN] Inno Setup installer failed.
            set "FAILED=1"
        ) else if exist "%ROOT%installer\OrbitBrowser-Setup.exe" (
            copy /Y "%ROOT%installer\OrbitBrowser-Setup.exe" "%OUT%\OrbitBrowser-Setup.exe" >nul
            echo [OK] Installer: %OUT%\OrbitBrowser-Setup.exe
        ) else (
            echo [WARN] Installer was not found after ISCC.
        )
    ) else (
        echo [INFO] Inno Setup not found. Skipping installer.
    )
) else (
    echo [INFO] OrbitBrowser.iss not found. Skipping installer.
)

echo.
echo [2/2] Android APK + AAB
echo.

if not exist "%ANDROID_DIR%\settings.gradle.kts" (
    echo [ERROR] Android project missing: %ANDROID_DIR%
    set "FAILED=1"
    goto DONE
)

set "JAVA_OK=0"
where java >nul 2>&1
if not errorlevel 1 set "JAVA_OK=1"
if "%JAVA_OK%"=="0" (
    echo [ERROR] Java/JDK not found. Install JDK 17 or newer.
    set "FAILED=1"
    goto DONE
)

if not defined ANDROID_HOME if defined ANDROID_SDK_ROOT set "ANDROID_HOME=%ANDROID_SDK_ROOT%"
if not defined ANDROID_HOME if exist "%LOCALAPPDATA%\Android\Sdk" set "ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk"
if not defined ANDROID_HOME if exist "%USERPROFILE%\AppData\Local\Android\Sdk" set "ANDROID_HOME=%USERPROFILE%\AppData\Local\Android\Sdk"

if not defined ANDROID_HOME (
    echo [ERROR] Android SDK not found.
    echo         Install Android Studio + SDK and set ANDROID_HOME,
    echo         or use the default Android Studio SDK location.
    set "FAILED=1"
    goto DONE
)

echo [INFO] Android SDK: %ANDROID_HOME%

REM Prefer project Gradle Wrapper if it exists.
if exist "%ANDROID_DIR%\gradlew.bat" (
    set "GRADLE_CMD=%ANDROID_DIR%\gradlew.bat"
    echo [INFO] Using Android Gradle Wrapper.
)

REM Otherwise use Gradle from PATH.
if not defined GRADLE_CMD (
    for /f "delims=" %%G in ('where gradle 2^>nul') do if not defined GRADLE_CMD set "GRADLE_CMD=%%G"
    if defined GRADLE_CMD echo [INFO] Using Gradle from PATH: !GRADLE_CMD!
)

REM Otherwise use cached local Gradle 8.7.
if not defined GRADLE_CMD if exist "%GRADLE_HOME%\bin\gradle.bat" (
    set "GRADLE_CMD=%GRADLE_HOME%\bin\gradle.bat"
    echo [INFO] Using cached Gradle 8.7.
)

REM Bootstrap Gradle 8.7 when needed.
if not defined GRADLE_CMD (
    echo [INFO] Gradle not found. Downloading Gradle 8.7 once...
    if not exist "%GRADLE_ZIP%" (
        powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -UseBasicParsing -Uri 'https://services.gradle.org/distributions/gradle-8.7-bin.zip' -OutFile '%GRADLE_ZIP%'"
        if errorlevel 1 (
            echo [ERROR] Could not download Gradle 8.7.
            set "FAILED=1"
            goto DONE
        )
    )

    if not exist "%GRADLE_HOME%\bin\gradle.bat" (
        if exist "%GRADLE_HOME%" rmdir /s /q "%GRADLE_HOME%"
        powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force '%GRADLE_ZIP%' '%TOOLS%'"
        if errorlevel 1 (
            echo [ERROR] Could not extract Gradle 8.7.
            set "FAILED=1"
            goto DONE
        )
    )

    if exist "%GRADLE_HOME%\bin\gradle.bat" (
        set "GRADLE_CMD=%GRADLE_HOME%\bin\gradle.bat"
        echo [OK] Gradle prepared: !GRADLE_CMD!
    ) else (
        echo [ERROR] Gradle 8.7 was extracted but gradle.bat was not found.
        set "FAILED=1"
        goto DONE
    )
)

if not defined GRADLE_CMD (
    echo [ERROR] No Gradle command is available.
    set "FAILED=1"
    goto DONE
)

if exist "%OUT%\OrbitBrowser-Android.apk" del /q "%OUT%\OrbitBrowser-Android.apk"
if exist "%OUT%\OrbitBrowser-Android.aab" del /q "%OUT%\OrbitBrowser-Android.aab"

pushd "%ANDROID_DIR%"
call "%GRADLE_CMD%" --no-daemon clean assembleRelease bundleRelease
set "ANDROID_EXIT=%ERRORLEVEL%"
popd

if not "%ANDROID_EXIT%"=="0" (
    echo [ERROR] Android Gradle build failed with code %ANDROID_EXIT%.
    set "FAILED=1"
    goto DONE
)

if exist "%ANDROID_DIR%\app\build\outputs\apk\release\app-release.apk" (
    copy /Y "%ANDROID_DIR%\app\build\outputs\apk\release\app-release.apk" "%OUT%\OrbitBrowser-Android.apk" >nul
    echo [OK] Android APK: %OUT%\OrbitBrowser-Android.apk
) else (
    echo [ERROR] APK was not produced.
    set "FAILED=1"
)

if exist "%ANDROID_DIR%\app\build\outputs\bundle\release\app-release.aab" (
    copy /Y "%ANDROID_DIR%\app\build\outputs\bundle\release\app-release.aab" "%OUT%\OrbitBrowser-Android.aab" >nul
    echo [OK] Android AAB: %OUT%\OrbitBrowser-Android.aab
) else (
    echo [WARN] AAB was not produced.
)

:DONE
echo.
echo ========================================================
if "%FAILED%"=="0" (
    echo BUILD COMPLETE
) else (
    echo BUILD FINISHED WITH ERRORS
)
echo Output: %OUT%
echo ========================================================
echo.
exit /b %FAILED%
