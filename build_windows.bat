@echo off
setlocal
cd /d "%~dp0"
py -3.13 -m pip install --upgrade pip
if errorlevel 1 exit /b 1
py -3.13 -m pip install PySide6 requests pyinstaller
if errorlevel 1 exit /b 1
py -3.13 build_exe.py
if errorlevel 1 exit /b 1
if not exist "gotovo" mkdir "gotovo"
copy /Y "build_out\OrbitBrowser.exe" "gotovo\OrbitBrowser.exe" >nul
if errorlevel 1 exit /b 1
echo.
echo Single-file OrbitBrowser.exe created in:
echo %CD%\gotovo\OrbitBrowser.exe
endlocal
