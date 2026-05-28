#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime, timedelta
import os
from pathlib import Path

class BotAdminPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("SigmaVPN Bot Admin Panel 🤖")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # Стиль
        self.root.configure(bg='#1e1e1e')
        style = ttk.Style()
        style.theme_use('clam')
        
        # Цвета
        self.bg_color = '#1e1e1e'
        self.fg_color = '#ffffff'
        self.accent_color = '#00d4ff'
        
        self.db_path = 'sigmavpn.db'
        
        # Создать интерфейс
        self.create_ui()
        self.load_data()
        
    def create_ui(self):
        """Создать интерфейс"""
        # Главное меню
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Открыть БД", command=self.open_db)
        file_menu.add_command(label="Экспортировать БД", command=self.export_db)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        # Верхняя панель с кнопками
        top_frame = tk.Frame(self.root, bg=self.bg_color)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(top_frame, text="🤖 SigmaVPN Bot Admin Panel", 
                font=("Arial", 16, "bold"), bg=self.bg_color, fg=self.accent_color).pack(side=tk.LEFT)
        
        # Кнопки управления
        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(btn_frame, text="🔄 Обновить", command=self.load_data, 
                 bg=self.accent_color, fg='black', font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="➕ Добавить пользователя", command=self.add_user,
                 bg='#00aa00', fg='white', font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Удалить", command=self.delete_user,
                 bg='#aa0000', fg='white', font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="📊 Статистика", command=self.show_stats,
                 bg='#aa00aa', fg='white', font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        # Вкладки
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка 1: Пользователи Telegram
        self.tab1 = ttk.Frame(notebook)
        notebook.add(self.tab1, text="👥 Пользователи Telegram")
        self.create_users_tab()
        
        # Вкладка 2: Платежи
        self.tab2 = ttk.Frame(notebook)
        notebook.add(self.tab2, text="💳 Платежи")
        self.create_payments_tab()
        
        # Вкладка 3: Подписки
        self.tab3 = ttk.Frame(notebook)
        notebook.add(self.tab3, text="📦 Подписки")
        self.create_subscriptions_tab()
        
        # Вкладка 4: Статистика
        self.tab4 = ttk.Frame(notebook)
        notebook.add(self.tab4, text="📈 Статистика")
        self.create_stats_tab()
        
    def create_users_tab(self):
        """Вкладка с пользователями"""
        # Таблица
        columns = ('ID', 'Telegram ID', 'Username', 'Имя', 'Дата регистрации')
        self.users_tree = ttk.Treeview(self.tab1, columns=columns, height=20)
        self.users_tree.column('#0', width=0, stretch=tk.NO)
        self.users_tree.column('ID', anchor=tk.W, width=50)
        self.users_tree.column('Telegram ID', anchor=tk.W, width=120)
        self.users_tree.column('Username', anchor=tk.W, width=150)
        self.users_tree.column('Имя', anchor=tk.W, width=150)
        self.users_tree.column('Дата регистрации', anchor=tk.W, width=150)
        
        self.users_tree.heading('#0', text='', anchor=tk.W)
        self.users_tree.heading('ID', text='ID', anchor=tk.W)
        self.users_tree.heading('Telegram ID', text='Telegram ID', anchor=tk.W)
        self.users_tree.heading('Username', text='Username', anchor=tk.W)
        self.users_tree.heading('Имя', text='Имя', anchor=tk.W)
        self.users_tree.heading('Дата регистрации', text='Дата регистрации', anchor=tk.W)
        
        self.users_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_payments_tab(self):
        """Вкладка с платежами"""
        columns = ('ID', 'Telegram ID', 'План', 'Сумма', 'Статус', 'Дата')
        self.payments_tree = ttk.Treeview(self.tab2, columns=columns, height=20)
        self.payments_tree.column('#0', width=0, stretch=tk.NO)
        self.payments_tree.column('ID', anchor=tk.W, width=50)
        self.payments_tree.column('Telegram ID', anchor=tk.W, width=120)
        self.payments_tree.column('План', anchor=tk.W, width=100)
        self.payments_tree.column('Сумма', anchor=tk.W, width=80)
        self.payments_tree.column('Статус', anchor=tk.W, width=100)
        self.payments_tree.column('Дата', anchor=tk.W, width=150)
        
        self.payments_tree.heading('#0', text='', anchor=tk.W)
        self.payments_tree.heading('ID', text='ID', anchor=tk.W)
        self.payments_tree.heading('Telegram ID', text='Telegram ID', anchor=tk.W)
        self.payments_tree.heading('План', text='План', anchor=tk.W)
        self.payments_tree.heading('Сумма', text='Сумма', anchor=tk.W)
        self.payments_tree.heading('Статус', text='Статус', anchor=tk.W)
        self.payments_tree.heading('Дата', text='Дата', anchor=tk.W)
        
        self.payments_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_subscriptions_tab(self):
        """Вкладка с подписками"""
        columns = ('ID', 'Telegram ID', 'План', 'Статус', 'Начало', 'Конец', 'Устройства')
        self.subs_tree = ttk.Treeview(self.tab3, columns=columns, height=20)
        self.subs_tree.column('#0', width=0, stretch=tk.NO)
        self.subs_tree.column('ID', anchor=tk.W, width=50)
        self.subs_tree.column('Telegram ID', anchor=tk.W, width=120)
        self.subs_tree.column('План', anchor=tk.W, width=100)
        self.subs_tree.column('Статус', anchor=tk.W, width=100)
        self.subs_tree.column('Начало', anchor=tk.W, width=150)
        self.subs_tree.column('Конец', anchor=tk.W, width=150)
        self.subs_tree.column('Устройства', anchor=tk.W, width=80)
        
        self.subs_tree.heading('#0', text='', anchor=tk.W)
        self.subs_tree.heading('ID', text='ID', anchor=tk.W)
        self.subs_tree.heading('Telegram ID', text='Telegram ID', anchor=tk.W)
        self.subs_tree.heading('План', text='План', anchor=tk.W)
        self.subs_tree.heading('Статус', text='Статус', anchor=tk.W)
        self.subs_tree.heading('Начало', text='Начало', anchor=tk.W)
        self.subs_tree.heading('Конец', text='Конец', anchor=tk.W)
        self.subs_tree.heading('Устройства', text='Устройства', anchor=tk.W)
        
        self.subs_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_stats_tab(self):
        """Вкладка со статистикой"""
        self.stats_frame = tk.Frame(self.tab4, bg=self.bg_color)
        self.stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def load_data(self):
        """Загрузить данные из БД"""
        if not os.path.exists(self.db_path):
            messagebox.showerror("Ошибка", f"БД не найдена: {self.db_path}")
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Загрузить пользователей
            self.users_tree.delete(*self.users_tree.get_children())
            cursor.execute("SELECT * FROM telegram_users ORDER BY created_at DESC")
            for row in cursor.fetchall():
                self.users_tree.insert('', 'end', values=(
                    row['id'], row['telegram_id'], row['username'], 
                    row['first_name'], row['created_at']
                ))
            
            # Загрузить платежи
            self.payments_tree.delete(*self.payments_tree.get_children())
            cursor.execute("SELECT * FROM telegram_payments ORDER BY created_at DESC")
            for row in cursor.fetchall():
                self.payments_tree.insert('', 'end', values=(
                    row['id'], row['telegram_id'], row['plan'], 
                    row['amount'], row['status'], row['created_at']
                ))
            
            # Загрузить подписки
            self.subs_tree.delete(*self.subs_tree.get_children())
            cursor.execute("SELECT * FROM telegram_subscriptions ORDER BY end_date DESC")
            for row in cursor.fetchall():
                self.subs_tree.insert('', 'end', values=(
                    row['id'], row['telegram_id'], row['plan'], 
                    row['status'], row['start_date'], row['end_date'], row['devices']
                ))
            
            conn.close()
            messagebox.showinfo("Успех", "Данные загружены!")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке: {str(e)}")
    
    def show_stats(self):
        """Показать статистику"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM telegram_users")
            users_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM telegram_payments WHERE status='completed'")
            payments_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM telegram_subscriptions WHERE status='active'")
            subs_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(amount) FROM telegram_payments WHERE status='completed'")
            total_revenue = cursor.fetchone()[0] or 0
            
            conn.close()
            
            # Очистить вкладку
            for widget in self.stats_frame.winfo_children():
                widget.destroy()
            
            # Показать статистику
            stats_text = f"""
📊 СТАТИСТИКА БОТА

👥 Всего пользователей: {users_count}
💳 Завершённых платежей: {payments_count}
📦 Активных подписок: {subs_count}
💰 Общий доход: {total_revenue} ₽

Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
            """
            
            label = tk.Label(self.stats_frame, text=stats_text, 
                           font=("Arial", 14), bg=self.bg_color, fg=self.accent_color,
                           justify=tk.LEFT)
            label.pack(padx=20, pady=20)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при получении статистики: {str(e)}")
    
    def add_user(self):
        """Добавить пользователя"""
        messagebox.showinfo("Информация", "Функция добавления пользователя будет реализована позже")
    
    def delete_user(self):
        """Удалить пользователя"""
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите пользователя для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", "Вы уверены?"):
            messagebox.showinfo("Информация", "Функция удаления будет реализована позже")
    
    def open_db(self):
        """Открыть БД"""
        file = filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db")])
        if file:
            self.db_path = file
            self.load_data()
    
    def export_db(self):
        """Экспортировать БД"""
        file = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite DB", "*.db")])
        if file:
            try:
                import shutil
                shutil.copy(self.db_path, file)
                messagebox.showinfo("Успех", f"БД экспортирована в {file}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при экспорте: {str(e)}")

if __name__ == '__main__':
    root = tk.Tk()
    app = BotAdminPanel(root)
    root.mainloop()
