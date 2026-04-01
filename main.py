import telebot
from telebot import types
import random
from dotenv import load_dotenv
import os

# Загружаем переменные из файла .env
load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(TOKEN)

# Словари данных
user_dicts = {}
user_states = {}


def main_menu():
    """
    Создает и возвращает главную клавиатуру навигационного меню.

    :return: Объект ReplyKeyboardMarkup с основными кнопками меню.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Добавить слово", "📑 Мой словарь")
    markup.add("✒️ Практика перевода", "📖 Теория")
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


def process_add_word(message):
    """
    Обрабатывает ввод пользователя для добавления нового слова в словарь.
    Ожидает формат 'Слово - Перевод'.

    :param message: Объект сообщения, содержащий добавляемое слово и перевод.
    """
    try:
        if '-' not in message.text:
            bot.send_message(message.chat.id, "Ошибка! Используйте дефис.")
            return
        en, ru = map(str.strip, message.text.split('-', 1))
        user_dicts[message.chat.id][en.lower()] = ru.lower()
        bot.send_message(message.chat.id, f"Сохранено: {en}")
    except Exception:
        bot.send_message(message.chat.id, "Ошибка ввода.")


def show_dictionary(uid):
    """
    Выводит пользователю список всех сохраненных им слов.

    :param uid: Уникальный идентификатор чата (пользователя).
    """
    words = user_dicts.get(uid, {})
    if not words:
        bot.send_message(uid, "Словарь пуст.")
        return
    res = "\n".join([f"{k} — {v}" for k, v in words.items()])
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