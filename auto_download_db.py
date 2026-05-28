#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Автоматическое скачивание БД с Railway
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def download_db_from_railway():
    """Скачать БД с Railway через SSH/Shell"""
    print("🚀 Автоматическое скачивание БД с Railway")
    print("=" * 60)
    
    project_dir = Path(__file__).parent
    db_file = project_dir / "sigmavpn.db"
    
    # Если БД уже существует, спросить
    if db_file.exists():
        print(f"✅ БД уже существует: {db_file}")
        print(f"📊 Размер: {db_file.stat().st_size / 1024 / 1024:.2f} MB")
        
        response = input("\n❓ Перезагрузить БД? (y/n): ").lower()
        if response != 'y':
            print("✅ Используется существующая БД")
            return True
    
    print("\n📥 Скачивание БД с Railway...")
    print("=" * 60)
    
    # Попытка 1: Через Railway CLI
    try:
        print("📝 Попытка 1: Через Railway CLI...")
        
        # Проверить, установлен ли Railway CLI
        result = subprocess.run(["railway", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Railway CLI найден")
            
            # Скачать БД
            print("📥 Скачиваю БД...")
            result = subprocess.run(
                ["railway", "run", "cat", "sigmavpn.db"],
                capture_output=True,
                cwd=str(project_dir)
            )
            
            if result.returncode == 0:
                # Сохранить БД
                with open(db_file, 'wb') as f:
                    f.write(result.stdout.encode() if isinstance(result.stdout, str) else result.stdout)
                
                print(f"✅ БД скачана: {db_file}")
                print(f"📊 Размер: {db_file.stat().st_size / 1024 / 1024:.2f} MB")
                return True
    except Exception as e:
        print(f"⚠️  Railway CLI не работает: {e}")
    
    # Попытка 2: Через Docker
    try:
        print("\n📝 Попытка 2: Через Docker...")
        
        # Проверить, установлен ли Docker
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker найден")
            print("📥 Скачиваю БД через Docker...")
            
            # Это сложнее, пропустим
            print("⚠️  Docker метод требует дополнительной настройки")
    except Exception as e:
        print(f"⚠️  Docker не работает: {e}")
    
    # Попытка 3: Создать пустую БД для тестирования
    print("\n📝 Попытка 3: Создание тестовой БД...")
    
    try:
        import sqlite3
        
        print("📝 Создаю пустую БД для тестирования...")
        
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        
        # Создать таблицы
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telegram_users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telegram_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                plan TEXT NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                payment_id TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES telegram_users(telegram_id)
            )
        """)
        
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
        
        print(f"✅ Тестовая БД создана: {db_file}")
        print(f"📊 Размер: {db_file.stat().st_size / 1024:.2f} KB")
        print("\n💡 Совет: Замените эту БД на реальную с Railway позже")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании БД: {e}")
        return False

def main():
    """Главная функция"""
    try:
        success = download_db_from_railway()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ БД готова!")
            print("=" * 60)
            print("\n🚀 Запускаю панель управления...")
            
            # Запустить панель
            exe_file = Path(__file__).parent / "dist" / "SigmaVPN_Bot_Admin.exe"
            
            if exe_file.exists():
                subprocess.Popen(str(exe_file))
                print("✅ Панель управления запущена!")
            else:
                print("📝 Запускаю через Python...")
                subprocess.Popen([sys.executable, "bot_admin_panel.py"], 
                               cwd=str(Path(__file__).parent))
                print("✅ Панель управления запущена!")
            
            return 0
        else:
            print("\n❌ Не удалось скачать БД")
            print("📝 Попробуйте скачать вручную с Railway")
            return 1
            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
