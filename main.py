import telebot
from telebot import types
import random
from dotenv import load_dotenv
import os
import sqlite3
import json

# Загружаем переменные из файла .env
load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

# Словари данных
user_states = {}


def init_db():
    """
    Инициализирует подключение к SQLite. Путь к БД берется из переменных окружения.
    """
    # Читаем путь из окружения (по умолчанию берем 'langbot.db' в текущей папке)
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


# Подключаемся
db_conn, db_cursor = init_db()


def main_menu():
    """
    Создает и возвращает главную клавиатуру навигационного меню.

    :return: Объект ReplyKeyboardMarkup с основными кнопками меню.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    WEB_APP_URL = "https://nnekrasov1.github.io/LangBot/"
    web_app_info = types.WebAppInfo(url=WEB_APP_URL)
    btn_web_app = types.KeyboardButton("📱 Открыть Mini App", web_app=web_app_info)
    markup.add(btn_web_app)
    return markup


@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    """
    Обрабатывает данные (JSON), присланные из Web App.
    """
    uid = message.chat.id
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get("action")

        if action == "add_word":
            en, ru = data["en"].lower(), data["ru"].lower()
            db_cursor.execute("INSERT INTO dictionary (user_id, word_en, word_ru) VALUES (?, ?, ?)", (uid, en, ru))
            db_conn.commit()
            bot.send_message(uid, f"✅ Успешно добавлено:\n*{en}* — {ru}", parse_mode="Markdown")

        elif action == "delete_word":
            en = data["en"].lower()
            # Проверяем, есть ли слово
            db_cursor.execute("SELECT id FROM dictionary WHERE user_id = ? AND word_en = ?", (uid, en))
            if db_cursor.fetchone():
                db_cursor.execute("DELETE FROM dictionary WHERE user_id = ? AND word_en = ?", (uid, en))
                db_conn.commit()
                bot.send_message(uid, f"🗑 Слово *{en}* удалено из словаря.", parse_mode="Markdown")
            else:
                bot.send_message(uid, f"❌ Слово *{en}* не найдено в вашем словаре.", parse_mode="Markdown")

        elif action == "show_dict":
            show_dictionary(uid)

        elif action == "practice":
            start_practice(uid)

        elif action == "theory":
            send_theory_text(uid)

    except Exception as e:
        bot.send_message(uid, "❌ Произошла ошибка при обработке данных из Mini App.")
        print(f"Web App Error: {e}")


@bot.message_handler(commands=['start'])
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    Обрабатывает команду /start. Приветствует пользователя.
    """
    uid = message.chat.id
    bot.send_message(
        uid,
        "Добро пожаловать в LangBot! 🇬🇧\nНажмите на кнопку ниже, чтобы открыть панель управления.",
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """
    Обработчик обычных текстовых сообщений.
    Используется только для проверки ответов в режиме практики.
    """
    uid = message.chat.id

    # Если пользователь сейчас проходит практику
    if uid in user_states:
        check_answer(message)
    else:
        # Если он просто так пишет в чат
        bot.send_message(uid, "Пожалуйста, используйте кнопку '📱 Открыть Mini App' 👇", reply_markup=main_menu())


def show_dictionary(uid):
    """
        Выводит пользователю список всех сохраненных им слов.

        :param uid: Уникальный идентификатор чата (пользователя).
    """
    db_cursor.execute("SELECT word_en, word_ru FROM dictionary WHERE user_id = ?", (uid,))
    rows = db_cursor.fetchall()

    if not rows:
        bot.send_message(uid, "Ваш словарь в базе данных пуст.")
        return

    res = "\n".join([f"{en} — {ru}" for en, ru in rows])
    bot.send_message(uid, f"Ваш словарь:\n{res}")


def start_practice(uid):
    """
    Запускает режим практики: выбирает случайное слово из словаря пользователя
    и предлагает его перевести.
    """
    db_cursor.execute("SELECT word_en, word_ru FROM dictionary WHERE user_id = ?", (uid,))
    rows = db_cursor.fetchall()

    if not rows:
        bot.send_message(uid, "Для начала добавьте слова через Mini App.")
        return

    # Выбираем случайную пару
    en, ru = random.choice(rows)
    user_states[uid] = ru  # Сохраняем правильный ответ (на русском) для проверки
    bot.send_message(uid, f"Переведите: *{en}*", parse_mode="Markdown")


def check_answer(message):
    """
    Проверяет правильность введенного пользователем перевода во время практики.

    :param message: Объект сообщения с ответом пользователя.
    """
    uid = message.chat.id
    correct = user_states.pop(uid)
    if message.text.lower().strip() == correct:
        bot.send_message(uid, "👍 Верно!")
    else:
        bot.send_message(uid, f"☝️ Нет. Правильно: {correct}")


def send_theory_text(uid):
    """
    Отправляет пользователю теоретический материал по правилам использования артиклей.

    :param uid: Уникальный идентификатор чата (пользователя).
    """
    text = (
        "Артикли (Articles)\n\n"

        "Артикль помогает нам понять, о каком именно предмете идёт речь. Например, если вы говорите, что хотите торт "
        "(любой), то будет так:.\n\n"

        "I want a cake. = Я хочу торт.\n\n"

        "Если же вы хотите сделать акцент на каком-то определённом торте, например, из пекарни в соседнем доме, "
        "— то в предложении уже будет другой артикль:\n\n"

        "I want the cake. = Я хочу (конкретный) торт.\n\n"

        "В английском языке выделяют три вида артиклей:\n\n"

        "1. неопределённый — a/an — употребляется с исчисляемыми существительными в единственном числе\n\n"
        "She read a book. = Она прочитала книгу.\n\n"

        "2. определённый — the — используется с исчисляемыми существительными в любом числе и с неисчисляемыми\n\n"
        "I visited the museums. = Я посетил музеи.\n\n"

        "3. нулевой артикль — перед исчисляемыми во множественном числе и неисчисляемыми существительными\n\n"

        "Knowledge is power. = Знание — сила.\n\n"
    )
    bot.send_message(uid, text, parse_mode="Markdown")


if __name__ == '__main__':
    bot.infinity_polling()
