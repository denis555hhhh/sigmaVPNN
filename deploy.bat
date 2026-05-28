@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ========================================
echo 🚀 ДЕПЛОЙ НА RAILWAY
echo ========================================
echo.

echo 📝 Добавляю файлы в git...
git add -A
if errorlevel 1 (
    echo ❌ Ошибка при добавлении файлов
    pause
    exit /b 1
)

echo ✅ Файлы добавлены

echo.
echo 💾 Коммитю изменения...
git commit -m "Fix app.py and restore website with Telegram links"
if errorlevel 1 (
    echo ❌ Ошибка при коммите
    pause
    exit /b 1
)

echo ✅ Коммит создан

echo.
echo 🌐 Пушу на GitHub...
git push
if errorlevel 1 (
    echo ❌ Ошибка при пуше
    pause
    exit /b 1
)

echo ✅ Запушено на GitHub

echo.
echo ========================================
echo ✨ ДЕПЛОЙ ЗАВЕРШЕН!
echo ========================================
echo.
echo 🔗 Railway автоматически перестроится
echo 📍 Сайт будет доступен на:
echo    https://sigmaVPNN-production.up.railway.app/
echo.
echo ⏱️  Ожидайте 2-3 минуты для завершения развертывания
echo.
pause
