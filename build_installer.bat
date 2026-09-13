@echo off
setlocal
cd /d "%~dp0"

if not exist "build_out\OrbitBrowser\OrbitBrowser.exe" (
  echo OrbitBrowser folder not found. Building EXE first...
  call build_windows.bat
  if errorlevel 1 exit /b 1
)

if not exist "installer" mkdir installer
where ISCC >nul 2>nul
if errorlevel 1 (
  echo Inno Setup compiler ISCC.exe not found.
  echo Install Inno Setup and add ISCC.exe to PATH, then run this file again.
  exit /b 1
)
ISCC.exe "OrbitBrowser.iss"
if errorlevel 1 exit /b 1
echo Installer: installer\OrbitBrowser-Setup.exe
endlocal
