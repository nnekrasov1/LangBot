import telebot
from telebot import types
import random
from dotenv import load_dotenv
import os
import sqlite3

# Загружаем переменные из файла .env
load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

# Словари данных
user_dicts = {}
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
    markup.add("➕ Добавить слово", "📑 Мой словарь")
    markup.add("✒️ Практика перевода", "🗑️ Удалить слово")
    markup.add("📖 Теория")
    return markup


def theory_menu():
    """
    Создает и возвращает клавиатуру подменю раздела 'Теория'.

    :return: Объект ReplyKeyboardMarkup с выбором тем и кнопкой 'Назад'.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Артикли", "👈 Назад")
    return markup


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    Обрабатывает команду /start. Приветствует пользователя и инициализирует его словарь.

    :param message: Объект сообщения от Telegram API.
    """
    uid = message.chat.id
    if uid not in user_dicts:
        user_dicts[uid] = {}
    bot.send_message(uid, "Добро пожаловать в LangBot!", reply_markup=main_menu())


@bot.message_handler(func=lambda message: True)
def handle_main_logic(message):
    """
    Основной обработчик текстовых сообщений. Управляет навигацией по меню
    и перенаправляет запросы в соответствующие функции.

    :param message: Объект сообщения от Telegram API.
    """
    uid = message.chat.id
    text = message.text

    if uid not in user_dicts:
        user_dicts[uid] = {}

    # Навигация и функции
    if text == "➕ Добавить слово":
        msg = bot.send_message(uid, "Введите: Word - Перевод")
        bot.register_next_step_handler(msg, process_add_word)

    elif text == "📑 Мой словарь":
        show_dictionary(uid)

    elif text == "✒️ Практика перевода":
        start_practice(uid)

    elif text == "📖 Теория":
        bot.send_message(uid, "Выберите тему:", reply_markup=theory_menu())

    elif text == "Артикли":
        send_theory_text(uid)

    elif text == "👈 Назад":
        bot.send_message(uid, "Главное меню:", reply_markup=main_menu())

    # Проверка ответа в режиме тренировки
    elif uid in user_states:
        check_answer(message)
    elif text == "🗑️ Удалить слово":
        msg = bot.send_message(uid, "Введите английское слово, которое хотите удалить:")
        bot.register_next_step_handler(msg, process_delete_word)


def process_add_word(message):
    """
        Обрабатывает ввод пользователя для добавления нового слова в словарь.
        Ожидает формат 'Слово - Перевод'.

        :param message: Объект сообщения, содержащий добавляемое слово и перевод.
    """
    try:
        en, ru = map(str.strip, message.text.split('-', 1))
        uid = message.chat.id

        # Записываем в базу
        db_cursor.execute(
            "INSERT INTO dictionary (user_id, word_en, word_ru) VALUES (?, ?, ?)",
            (uid, en.lower(), ru.lower())
        )
        db_conn.commit()

        bot.send_message(uid, f"Сохранено в базу: {en}")
    except Exception:
        bot.send_message(message.chat.id, "Ошибка! Используйте формат: Слово - Перевод")


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

    :param uid: Уникальный идентификатор чата (пользователя).
    """
    words = user_dicts.get(uid, {})
    if not words:
        bot.send_message(uid, "Для начала добавьте слова.")
        return
    en = random.choice(list(words.keys()))
    user_states[uid] = words[en]
    bot.send_message(uid, f"Переведите: {en}")


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


def process_delete_word(message):
    """
    Удаляет выбранное слово из базы данных SQLite для текущего пользователя.

    :param message: Объект сообщения с английским словом для удаления.
    """
    uid = message.chat.id
    word_to_delete = message.text.lower().strip()

    try:
        # Проверяем, есть ли такое слово
        db_cursor.execute(
            "SELECT id FROM dictionary WHERE user_id = ? AND word_en = ?",
            (uid, word_to_delete)
        )
        row = db_cursor.fetchone()

        if row:
            db_cursor.execute(
                "DELETE FROM dictionary WHERE user_id = ? AND word_en = ?",
                (uid, word_to_delete)
            )
            db_conn.commit()
            bot.send_message(uid, f"✅ Слово '{word_to_delete}' успешно удалено.")
        else:
            bot.send_message(uid, f"❌ Слово '{word_to_delete}' не найдено в вашем словаре.")

    except Exception as e:
        bot.send_message(uid, "⚠️ Произошла ошибка при обращении к базе данных.")

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