@echo off
setlocal
cd /d "%~dp0"
set "REPO=%~1"
if "%REPO%"=="" set /p REPO=Укажи путь к локальной папке клона OrbitBrowsers: 
if not exist "%REPO%\.git" (
  echo Не найден Git-репозиторий: %REPO%
  pause
  exit /b 1
)
robocopy "%~dp0" "%REPO%" /E /XD ".git" "build_out" "build_work" "build_spec" "output" /XF "sync_to_github.bat" >nul
cd /d "%REPO%"
git add .
git commit -m "Orbit Browser 2.3: sync GUI, site and release files"
git push
if errorlevel 1 (
  echo Не удалось отправить изменения. Проверь GitHub login/remote и права записи.
  pause
  exit /b 1
)
echo Готово: GitHub обновлен.
pause
