@echo off
setlocal
cd /d "%~dp0"
py -3.13 -m pip install --upgrade pip
py -3.13 -m pip install PySide6 requests pyinstaller
if errorlevel 1 exit /b 1
py -3.13 build_exe.py
if errorlevel 1 exit /b 1
echo.
echo OrbitBrowser folder created in build_out\OrbitBrowser\
echo The executable is build_out\OrbitBrowser\OrbitBrowser.exe
endlocal
