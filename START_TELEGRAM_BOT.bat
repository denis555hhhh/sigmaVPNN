@echo off
chcp 65001 >nul
title SigmaVPN Telegram Bot
cd /d "%~dp0"

echo.
echo ========================================
echo   🤖 SigmaVPN Telegram Bot
echo ========================================
echo.
echo 📱 Telegram Bot: @SigmaVPN2134_BOT
echo 💳 Yoomoney: 4100118775331265
echo.
echo Запуск бота...
echo.

python telegram_bot.py

pause
