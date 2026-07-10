import os
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

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
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Список"), KeyboardButton(text="➕ Добавить")],
        [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="📊 Статистика")]
    ],
    resize_keyboard=True
)

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    cursor.execute(
        "INSERT OR IGNORE INTO users (telegram_id, username, created_at) VALUES (?, ?, ?)",
        (msg.from_user.id, msg.from_user.username, datetime.now().isoformat())
    )
    conn.commit()
    
    await msg.answer(
        "🚀 *Бот готов к работе!*\n\n"
        "Используй кнопки внизу 👇",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.message_handler(lambda msg: msg.text == "📋 Список")
async def show_list(msg: types.Message):
    cursor.execute("SELECT id, name, price FROM items ORDER BY id DESC LIMIT 20")
    items = cursor.fetchall()
    
    if not items:
        await msg.answer("📭 База пуста. Добавь первую запись!")
        return
    
    text = "📋 *Последние записи:*\n\n"
    for item in items:
        text += f"`#{item[0]}` *{item[1]}* — {item[2]} руб.\n"
    
    await msg.answer(text, parse_mode="Markdown")

@dp.message_handler(lambda msg: msg.text == "➕ Добавить")
async def add_prompt(msg: types.Message):
    await msg.answer(
        "✏️ *Добавление записи*\n\n"
        "Отправь в формате:\n"
        "`Название | Цена | Описание`\n\n"
        "Пример:\n"
        "`iPhone 15 | 99900 | Новый телефон`",
        parse_mode="Markdown"
    )

@dp.message_handler(lambda msg: msg.text and " | " in msg.text)
async def process_add(msg: types.Message):
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
        
        await msg.answer(
            f"✅ *Добавлено!*\n\n📦 {name}\n💰 {price} руб.\n📝 {description}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await msg.answer(f"❌ Ошибка: {str(e)}\n\nИспользуй формат:\n`Название | Цена | Описание`", parse_mode="Markdown")

@dp.message_handler(lambda msg: msg.text == "🔍 Поиск")
async def search_prompt(msg: types.Message):
    await msg.answer("🔍 *Введи текст для поиска*", parse_mode="Markdown")

@dp.message_handler(lambda msg: msg.text and not msg.text.startswith("/") and msg.text not in ["📋 Список", "➕ Добавить", "🔍 Поиск", "📊 Статистика"])
async def search(msg: types.Message):
    cursor.execute(
        "SELECT id, name, price FROM items WHERE name LIKE ? OR description LIKE ? LIMIT 10",
        (f"%{msg.text}%", f"%{msg.text}%")
    )
    items = cursor.fetchall()
    
    if not items:
        await msg.answer(f"🔍 Ничего не найдено: *{msg.text}*", parse_mode="Markdown")
        return
    
    text = f"🔍 *Результаты:* {msg.text}\n\n"
    for item in items:
        text += f"`#{item[0]}` *{item[1]}* — {item[2]} руб.\n"
    
    await msg.answer(text, parse_mode="Markdown")

@dp.message_handler(lambda msg: msg.text == "📊 Статистика")
async def stats(msg: types.Message):
    cursor.execute("SELECT COUNT(*) FROM items")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    
    await msg.answer(
        f"📊 *Статистика:*\n\n"
        f"👥 Пользователей: {users}\n"
        f"📦 Записей: {total}",
        parse_mode="Markdown"
    )

@dp.message_handler(commands=['help'])
async def help_cmd(msg: types.Message):
    await msg.answer(
        "📖 *Команды:*\n"
        "/start - Главное меню\n"
        "/help - Помощь\n\n"
        "Или нажимай кнопки 👇",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
