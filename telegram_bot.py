#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_TOKEN = "8934651350:AAG4pGwPnY_5nSwV-L141mdhxC-BnEqEJK8"
ADMIN_ID = 8521842720
БД_ПУТЬ = os.getenv('DATABASE_PATH', 'sigmavpn.db')

# Подписки и цены
PLANS = {
    'basic': {
        'name': '🟢 Базовая',
        'price': 99,
        'duration': 7,
        'description': '7 дней, 1 устройство'
    },
    'standard': {
        'name': '🔵 Стандарт',
        'price': 299,
        'duration': 30,
        'description': '30 дней, 3 устройства'
    },
    'premium': {
        'name': '🟣 Премиум',
        'price': 799,
        'duration': 365,
        'description': '365 дней, 5 устройств'
    }
}

# ==================== БД ====================
def подключиться():
    """Подключиться к БД"""
    conn = sqlite3.connect(БД_ПУТЬ)
    conn.row_factory = sqlite3.Row
    return conn

def инициализировать_бд():
    """Инициализировать таблицы для бота"""
    conn = подключиться()
    cursor = conn.cursor()
    
    # Таблица пользователей Telegram
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telegram_users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица платежей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            plan TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (telegram_id) REFERENCES telegram_users(telegram_id)
        )
    """)
    
    # Таблица подписок Telegram
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telegram_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            plan TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_date TIMESTAMP,
            FOREIGN KEY (telegram_id) REFERENCES telegram_users(telegram_id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✓ БД инициализирована")

# ==================== КОМАНДЫ ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    telegram_id = user.id
    
    # Сохранить пользователя в БД
    conn = подключиться()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO telegram_users (telegram_id, username, first_name)
            VALUES (?, ?, ?)
        """, (telegram_id, user.username, user.first_name))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Пользователь уже существует
    
    conn.close()
    
    # Приветственное сообщение
    welcome_text = f"""
👋 Привет, {user.first_name}!

Добро пожаловать в **SigmaVPN** 🚀

Я помогу вам выбрать подписку и подключиться к VPN.

Выберите действие:
"""
    
    keyboard = [
        [InlineKeyboardButton("📦 Выбрать подписку", callback_data='show_plans')],
        [InlineKeyboardButton("📊 Мои подписки", callback_data='my_subscriptions')],
        [InlineKeyboardButton("❓ Помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать доступные подписки"""
    query = update.callback_query
    await query.answer()
    
    text = "💳 **Выберите подписку:**\n\n"
    
    keyboard = []
    for plan_id, plan_info in PLANS.items():
        text += f"{plan_info['name']}\n"
        text += f"💰 {plan_info['price']} ₽\n"
        text += f"📅 {plan_info['description']}\n\n"
        
        keyboard.append([
            InlineKeyboardButton(
                f"{plan_info['name']} - {plan_info['price']} ₽",
                callback_data=f'buy_{plan_id}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='back_to_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def buy_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Купить подписку"""
    query = update.callback_query
    await query.answer()
    
    plan_id = query.data.split('_')[1]
    plan_info = PLANS[plan_id]
    
    telegram_id = query.from_user.id
    
    # Сохранить платёж в БД
    conn = подключиться()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO payments (telegram_id, plan, amount, status)
        VALUES (?, ?, ?, 'pending')
    """, (telegram_id, plan_id, plan_info['price']))
    
    payment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Сообщение об оплате
    text = f"""
✅ **Вы выбрали подписку:**

{plan_info['name']}
💰 Цена: {plan_info['price']} ₽
📅 Период: {plan_info['description']}

**Способы оплаты:**
1. 💳 Карта (Yandex.Kassa)
2. 💰 Яндекс.Касса
3. 📱 Мобильный платёж

⚠️ Функция оплаты в разработке.
Пока оплачивайте вручную и напишите админу.

Админ: @sigmavpn_admin
"""
    
    keyboard = [
        [InlineKeyboardButton("💳 Оплатить", callback_data=f'pay_{payment_id}')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='show_plans')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def my_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать мои подписки"""
    query = update.callback_query
    await query.answer()
    
    telegram_id = query.from_user.id
    
    conn = подключиться()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT plan, status, start_date, end_date FROM telegram_subscriptions
        WHERE telegram_id = ? AND status = 'active'
        ORDER BY end_date DESC
    """, (telegram_id,))
    
    subscriptions = cursor.fetchall()
    conn.close()
    
    if not subscriptions:
        text = "❌ У вас нет активных подписок\n\nКупите подписку, чтобы начать пользоваться VPN!"
    else:
        text = "📊 **Ваши активные подписки:**\n\n"
        for sub in subscriptions:
            plan_info = PLANS.get(sub['plan'], {})
            text += f"{plan_info.get('name', 'Неизвестная подписка')}\n"
            text += f"✅ Статус: {sub['status']}\n"
            text += f"📅 До: {sub['end_date']}\n\n"
    
    keyboard = [
        [InlineKeyboardButton("📦 Купить ещё", callback_data='show_plans')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь"""
    query = update.callback_query
    await query.answer()
    
    text = """
❓ **Помощь**

**Как пользоваться SigmaVPN?**

1. 📦 Выберите подписку
2. 💳 Оплатите
3. 📥 Получите VPN конфиг
4. 🔗 Подключитесь к VPN

**Поддерживаемые протоколы:**
- WireGuard
- OpenVPN

**Вопросы?**
Напишите админу: @sigmavpn_admin

**Контакты:**
📧 Email: support@sigmavpn.com
💬 Telegram: @sigmavpn_admin
"""
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    query = update.callback_query
    await query.answer()
    
    text = """
🏠 **Главное меню**

Выберите действие:
"""
    
    keyboard = [
        [InlineKeyboardButton("📦 Выбрать подписку", callback_data='show_plans')],
        [InlineKeyboardButton("📊 Мои подписки", callback_data='my_subscriptions')],
        [InlineKeyboardButton("❓ Помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок"""
    query = update.callback_query
    
    if query.data == 'show_plans':
        await show_plans(update, context)
    elif query.data.startswith('buy_'):
        await buy_plan(update, context)
    elif query.data == 'my_subscriptions':
        await my_subscriptions(update, context)
    elif query.data == 'help':
        await help_command(update, context)
    elif query.data == 'back_to_menu':
        await back_to_menu(update, context)

# ==================== ЗАПУСК ====================
def main():
    """Запуск бота"""
    print("🤖 Запуск Telegram бота SigmaVPN...")
    
    # Инициализировать БД
    инициализировать_бд()
    
    # Создать приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавить обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Запустить бота
    print("✓ Бот запущен!")
    print(f"📱 Telegram ID админа: {ADMIN_ID}")
    application.run_polling()

if __name__ == '__main__':
    main()
