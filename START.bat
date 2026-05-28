@echo off
chcp 65001 >nul
cls

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  🚀 SigmaVPN Admin Panel - Полный автозапуск              ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Проверить Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не установлен!
    echo 📝 Установите Python с https://python.org
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Запустить скрипт скачивания БД и запуска панели
echo 🚀 Запускаю автоматическую настройку...
echo.

python auto_download_db.py

if errorlevel 1 (
    echo.
    echo ❌ Ошибка при запуске
    pause
    exit /b 1
)

exit /b 0
