import os
import sqlite3
from datetime import datetime
import telebot
from telebot import types

TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# База данных
conn = sqlite3.connect('data.db', check_same_thread=False)
cursor = conn.cursor()

# Создаём таблицы
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        created_at TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        description TEXT,
        created_at TEXT
    )
''')
conn.commit()

# Кнопки
keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.row("📋 Список", "➕ Добавить")
keyboard.row("🔍 Поиск", "📊 Статистика")

@bot.message_handler(commands=['start'])
def start(msg):
    cursor.execute(
        "INSERT OR IGNORE INTO users (telegram_id, username, created_at) VALUES (?, ?, ?)",
        (msg.from_user.id, msg.from_user.username, datetime.now().isoformat())
    )
    conn.commit()
    
    bot.send_message(
        msg.chat.id,
        "🚀 *Бот готов к работе!*\n\nИспользуй кнопки внизу 👇",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@bot.message_handler(func=lambda msg: msg.text == "📋 Список")
def show_list(msg):
    cursor.execute("SELECT id, name, price FROM items ORDER BY id DESC LIMIT 20")
    items = cursor.fetchall()
    
    if not items:
        bot.send_message(msg.chat.id, "📭 База пуста. Добавь первую запись!")
        return
    
    text = "📋 *Последние записи:*\n\n"
    for item in items:
        text += f"`#{item[0]}` *{item[1]}* — {item[2]} руб.\n"
    
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "➕ Добавить")
def add_prompt(msg):
    bot.send_message(
        msg.chat.id,
        "✏️ *Добавление записи*\n\n"
        "Отправь в формате:\n"
        "`Название | Цена | Описание`\n\n"
        "Пример:\n"
        "`iPhone 15 | 99900 | Новый телефон`",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda msg: msg.text and " | " in msg.text)
def process_add(msg):
    try:
        parts = msg.text.split(" | ")
        name = parts[0].strip()
        price = float(parts[1].strip())
        description = parts[2].strip() if len(parts) > 2 else ""
        
        cursor.execute(
            "INSERT INTO items (name, price, description, created_at) VALUES (?, ?, ?, ?)",
            (name, price, description, datetime.now().isoformat())
        )
        conn.commit()
        
        bot.send_message(
            msg.chat.id,
            f"✅ *Добавлено!*\n\n📦 {name}\n💰 {price} руб.\n📝 {description}",
            parse_mode="Markdown"
        )
    except:
        bot.send_message(
            msg.chat.id,
            "❌ Ошибка! Используй формат:\n`Название | Цена | Описание`",
            parse_mode="Markdown"
        )

@bot.message_handler(func=lambda msg: msg.text == "🔍 Поиск")
def search_prompt(msg):
    bot.send_message(msg.chat.id, "🔍 *Введи текст для поиска*", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text and not msg.text.startswith("/") and msg.text not in ["📋 Список", "➕ Добавить", "🔍 Поиск", "📊 Статистика"])
def search(msg):
    cursor.execute(
        "SELECT id, name, price FROM items WHERE name LIKE ? OR description LIKE ? LIMIT 10",
        (f"%{msg.text}%", f"%{msg.text}%")
    )
    items = cursor.fetchall()
    
    if not items:
        bot.send_message(msg.chat.id, f"🔍 Ничего не найдено: *{msg.text}*", parse_mode="Markdown")
        return
    
    text = f"🔍 *Результаты:* {msg.text}\n\n"
    for item in items:
        text += f"`#{item[0]}` *{item[1]}* — {item[2]} руб.\n"
    
    bot.send_message(msg.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📊 Статистика")
def stats(msg):
    cursor.execute("SELECT COUNT(*) FROM items")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    
    bot.send_message(
        msg.chat.id,
        f"📊 *Статистика:*\n\n"
        f"👥 Пользователей: {users}\n"
        f"📦 Записей: {total}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['help'])
def help_cmd(msg):
    bot.send_message(
        msg.chat.id,
        "📖 *Команды:*\n"
        "/start - Главное меню\n"
        "/help - Помощь\n\n"
        "Или нажимай кнопки 👇",
        parse_mode="Markdown"
    )

print("🤖 Бот запущен!")
bot.polling()
