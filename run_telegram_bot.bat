@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 🤖 Запуск Telegram бота SigmaVPN...
echo.

python telegram_bot.py

pause
