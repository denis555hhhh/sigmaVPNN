#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для создания EXE файла из bot_admin_panel.py
Требует: pip install pyinstaller
"""

import os
import subprocess
import sys

def build_exe():
    """Создать EXE файл"""
    print("🔨 Создание EXE файла...")
    print("=" * 50)
    
    # Проверить наличие pyinstaller
    try:
        import PyInstaller
    except ImportError:
        print("❌ PyInstaller не установлен!")
        print("Установите: pip install pyinstaller")
        return False
    
    # Команда для создания EXE
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--icon=NONE',
        '--name=SigmaVPN_Bot_Admin',
        '--add-data=sigmavpn.db:.',
        'bot_admin_panel.py'
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ EXE файл создан успешно!")
        print("📁 Файл находится в папке: dist/SigmaVPN_Bot_Admin.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка при создании EXE: {e}")
        return False

if __name__ == '__main__':
    build_exe()
