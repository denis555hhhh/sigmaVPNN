#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import sqlite3
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import uuid
from urllib.parse import urlencode

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

# Yoomoney конфигурация
YOOMONEY_WALLET = "4100118775331265"  # Номер кошелька Yoomoney
YOOMONEY_BASE_URL = "https://yoomoney.ru/quickpay/confirm.xml"

# Подписки и цены
PLANS = {
    'basic': {
        'name': '🟢 Базовая',
        'price': 99,
        'duration': 7,
        'description': '7 дней, 1 устройство',
        'devices': 1
    },
    'standard': {
        'name': '🔵 Стандарт',
        'price': 299,
        'duration': 30,
        'description': '30 дней, 3 устройства',
        'devices': 3
    },
    'premium': {
        'name': '🟣 Премиум',
        'price': 799,
        'duration': 365,
        'description': '365 дней, 5 устройств',
        'devices': 5
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
        CREATE TABLE IF NOT EXISTS telegram_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            plan TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_id TEXT UNIQUE,
            yandex_payment_id TEXT,
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
            devices INTEGER DEFAULT 1,
            FOREIGN KEY (telegram_id) REFERENCES telegram_users(telegram_id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✓ БД инициализирована")

# ==================== YOOMONEY ====================
def создать_ссылку_оплаты(plan_id):
    """Создать вечную ссылку на оплату через Yoomoney"""
    plan_info = PLANS[plan_id]
    
    # Параметры ссылки
    params = {
        'receiver': YOOMONEY_WALLET,
        'quickpay-form': 'shop',
        'targets': f'SigmaVPN {plan_info["name"]}',
        'sum': plan_info['price'],
        'currency': 'RUB'
    }
    
    # Построить ссылку
    from urllib.parse import urlencode
    payment_url = f"{YOOMONEY_BASE_URL}?{urlencode(params)}"
    
    return payment_url

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
    
    try:
        plan_id = query.data.split('_')[1]
        plan_info = PLANS[plan_id]
        telegram_id = query.from_user.id
        
        # Создать ссылку на оплату
        payment_url = создать_ссылку_оплаты(plan_id)
        
        # Сохранить платёж в БД
        conn = подключиться()
        cursor = conn.cursor()
        
        payment_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO telegram_payments (telegram_id, plan, amount, payment_id, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (telegram_id, plan_id, plan_info['price'], payment_id))
        
        conn.commit()
        conn.close()
        
        # Сообщение об оплате
        text = f"""
✅ **Вы выбрали подписку:**

{plan_info['name']}
💰 Цена: {plan_info['price']} ₽
📅 Период: {plan_info['description']}

🔗 **Нажмите кнопку ниже для оплаты:**
"""
        
        keyboard = [
            [InlineKeyboardButton("💳 Оплатить через Yoomoney", url=payment_url)],
            [InlineKeyboardButton("✅ Я оплатил", callback_data=f'confirm_payment_{payment_id}')],
            [InlineKeyboardButton("⬅️ Назад", callback_data='show_plans')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Ошибка в buy_plan: {e}")
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтвердить платёж"""
    query = update.callback_query
    await query.answer()
    
    try:
        payment_id = query.data.split('_')[2]
        telegram_id = query.from_user.id
        
        # Проверить платёж в БД
        conn = подключиться()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT plan, status FROM telegram_payments
            WHERE payment_id = ? AND telegram_id = ?
        """, (payment_id, telegram_id))
        
        payment = cursor.fetchone()
        conn.close()
        
        if not payment:
            text = "❌ Платёж не найден"
        elif payment['status'] == 'completed':
            text = "✅ Платёж уже подтверждён!\n\nВаша подписка активирована."
        else:
            # Активировать подписку
            plan_info = PLANS[payment['plan']]
            start_date = datetime.now()
            end_date = start_date + timedelta(days=plan_info['duration'])
            
            conn = подключиться()
            cursor = conn.cursor()
            
            # Деактивировать старые подписки
            cursor.execute("""
                UPDATE telegram_subscriptions 
                SET status = 'expired'
                WHERE telegram_id = ? AND status = 'active'
            """, (telegram_id,))
            
            # Создать новую подписку
            cursor.execute("""
                INSERT INTO telegram_subscriptions (telegram_id, plan, status, start_date, end_date, devices)
                VALUES (?, ?, 'active', ?, ?, ?)
            """, (telegram_id, payment['plan'], start_date.isoformat(), end_date.isoformat(), plan_info['devices']))
            
            # Обновить статус платежа
            cursor.execute("""
                UPDATE telegram_payments SET status = 'completed'
                WHERE payment_id = ?
            """, (payment_id,))
            
            conn.commit()
            conn.close()
            
            text = f"""
🧡 **Спасибо за покупку!**

Подписка активирована: {plan_info['name']}
📅 Период: {plan_info['description']}
📱 Устройств: {plan_info['devices']}

**Чтобы получить VPN конфиг, напишите разработчику:**

📧 **@slogg12** (Telegram)
📧 **support@sigmavpn.com** (Email)

Укажите ваш Telegram ID и выбранный тариф.
"""
        
        keyboard = [
            [InlineKeyboardButton("📊 Мои подписки", callback_data='my_subscriptions')],
            [InlineKeyboardButton("⬅️ Назад", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Ошибка в confirm_payment: {e}")
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def my_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать мои подписки"""
    query = update.callback_query
    await query.answer()
    
    try:
        telegram_id = query.from_user.id
        
        conn = подключиться()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT plan, status, start_date, end_date, devices FROM telegram_subscriptions
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
                end_date = datetime.fromisoformat(sub['end_date'])
                days_left = (end_date - datetime.now()).days
                
                text += f"{plan_info.get('name', 'Неизвестная подписка')}\n"
                text += f"✅ Статус: {sub['status']}\n"
                text += f"📱 Устройств: {sub['devices']}\n"
                text += f"⏰ Осталось: {days_left} дней\n"
                text += f"📅 До: {end_date.strftime('%d.%m.%Y')}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("📦 Купить ещё", callback_data='show_plans')],
            [InlineKeyboardButton("⬅️ Назад", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Ошибка в my_subscriptions: {e}")
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь"""
    query = update.callback_query
    await query.answer()
    
    try:
        text = """
❓ **Помощь**

**Как пользоваться SigmaVPN?**

1. 📦 Выберите подписку
2. 💳 Оплатите через Yoomoney
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
🌐 Сайт: https://sigmavpnn-production.up.railway.app
"""
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Назад", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Ошибка в help_command: {e}")
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в главное меню"""
    query = update.callback_query
    await query.answer()
    
    try:
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
    except Exception as e:
        logger.error(f"Ошибка в back_to_menu: {e}")
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок"""
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == 'show_plans':
            await show_plans(update, context)
        elif query.data.startswith('buy_'):
            await buy_plan(update, context)
        elif query.data.startswith('confirm_payment_'):
            await confirm_payment(update, context)
        elif query.data == 'my_subscriptions':
            await my_subscriptions(update, context)
        elif query.data == 'help':
            await help_command(update, context)
        elif query.data == 'back_to_menu':
            await back_to_menu(update, context)
    except Exception as e:
        logger.error(f"Ошибка в обработчике кнопок: {e}")
        text = """
🧡 **Спасибо за покупку!**

Напишите разработчику, чтобы получить конфиг:

📧 **@slogg12** (Telegram)
📧 **support@sigmavpn.com** (Email)

Укажите ваш Telegram ID и выбранный тариф.
"""
        try:
            await query.edit_message_text(text, parse_mode='Markdown')
        except:
            pass

# ==================== ЗАПУСК ====================
def main():
    """Запуск бота"""
    print("🤖 Запуск Telegram бота SigmaVPN...")
    print(f"📱 Telegram ID админа: {ADMIN_ID}")
    print(f"💳 Yoomoney кошелёк: {YOOMONEY_WALLET}")
    print("=" * 50)
    
    # Инициализировать БД
    инициализировать_бд()
    
    # Создать приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавить обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Запустить бота
    print("✓ Бот запущен и готов к работе!")
    print("=" * 50)
    application.run_polling()

if __name__ == '__main__':
    main()
