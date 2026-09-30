@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Yavoz

echo.
echo   Yavoz - обработка файлов с Яндекс.Диска
echo   ---------------------------------------
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo   [!] Python не найден.
  echo.
  echo   Установите его с https://www.python.org/downloads/
  echo   При установке ОБЯЗАТЕЛЬНО отметьте галочку
  echo   "Add python.exe to PATH" на первом экране.
  echo.
  echo   Потом запустите этот файл ещё раз.
  echo.
  pause
  exit /b 1
)

if not exist ".venv" (
  echo   Первый запуск: готовлю окружение, это займёт минуту...
  python -m venv .venv
  if errorlevel 1 (
    echo   [!] Не удалось создать окружение.
    pause
    exit /b 1
  )
)

echo   Проверяю библиотеки...
".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
  echo   [!] Не удалось установить библиотеки. Проверьте интернет.
  pause
  exit /b 1
)

echo.
echo   Открываю http://127.0.0.1:8765 в браузере.
echo   Это окно НЕ закрывайте, пока работаете с приложением.
echo   Чтобы остановить - закройте окно или нажмите Ctrl+C.
echo.

start "" http://127.0.0.1:8765
".venv\Scripts\python.exe" -m yavoz

echo.
echo   Приложение остановлено.
pause
