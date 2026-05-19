import telebot
from telebot import types
import sqlite3
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

# Загружаем переменные окружения
load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

# Инициализация flask api
app = Flask(__name__)
CORS(app)  # Разрешаем запросы с GitHub Pages


def init_db():
    """
    Инициализирует подключение к SQLite. Путь к БД берется из переменных окружения.
    """
    db_path = os.getenv('DB_PATH', 'langbot.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dictionary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            word_en TEXT,
            word_ru TEXT
        )
    ''')
    conn.commit()
    return conn, cursor


db_conn, db_cursor = init_db()


@app.route('/api/get_dict', methods=['GET'])
def api_get_dict():
    uid = request.args.get('uid')
    db_cursor.execute("SELECT word_en, word_ru FROM dictionary WHERE user_id = ?", (uid,))
    rows = db_cursor.fetchall()
    words = [{"en": row[0], "ru": row[1]} for row in rows]
    return jsonify({"status": "ok", "words": words})


@app.route('/api/add_word', methods=['POST'])
def api_add_word():
    data = request.json
    uid, en, ru = data.get('uid'), data.get('en').lower(), data.get('ru').lower()
    db_cursor.execute("INSERT INTO dictionary (user_id, word_en, word_ru) VALUES (?, ?, ?)", (uid, en, ru))
    db_conn.commit()
    return jsonify({"status": "ok", "message": f"Слово '{en}' добавлено!"})


@app.route('/api/delete_word', methods=['POST'])
def api_delete_word():
    data = request.json
    uid, en = data.get('uid'), data.get('en').lower()

    db_cursor.execute("SELECT id FROM dictionary WHERE user_id = ? AND word_en = ?", (uid, en))
    if db_cursor.fetchone():
        db_cursor.execute("DELETE FROM dictionary WHERE user_id = ? AND word_en = ?", (uid, en))
        db_conn.commit()
        return jsonify({"status": "ok", "message": f"Слово '{en}' удалено."})
    else:
        return jsonify({"status": "error", "message": "Слово не найдено в словаре."})


def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    WEB_APP_URL = "https://nnekrasov1.github.io/LangBot/"
    web_app_info = types.WebAppInfo(url=WEB_APP_URL)
    markup.add(types.KeyboardButton("📱 Открыть Mini App", web_app=web_app_info))
    return markup


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    Обрабатывает команду /start. Приветствует пользователя.
    """
    bot.send_message(
        message.chat.id,
        "Добро пожаловать в LangBot! 🇬🇧\nНажмите на кнопку ниже, чтобы открыть приложение.",
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    bot.send_message(message.chat.id, "Всё управление теперь происходит внутри Mini App 👇", reply_markup=main_menu())


def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    print("Бот и API сервер запущены...")
    bot.infinity_polling()
