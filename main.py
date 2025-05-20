import asyncio
import logging
import aiomysql
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from flask import Flask
from threading import Thread

API_TOKEN = '7584543228:AAFIxZ8BRW3DKDN5mgPqjNb_VBa4bW8Q8dE'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

CHANNEL_ID = -1002279944530  # Замените на ID вашего канала

# Подключение к базе данных
async def get_anime_by_code(code: str):
    try:
        conn = await aiomysql.connect(
            host='mysql-lakalut.alwaysdata.net',
            port=3306,
            user='lakalut',
            password='cfrfvjnj1201',
            db='lakalut_tbot'
        )
        async with conn.cursor() as cur:
            await cur.execute("SELECT title, genre, image_url FROM anime WHERE code = %s", (code,))
            result = await cur.fetchone()
            await conn.ensure_closed()
            if result:
                text = f"Название: {result[0]}\nЖанр: {result[1]}"
                image_url = result[2]
                return text, image_url
            else:
                return "Аниме с таким кодом не найдено.", None
    except Exception as e:
        return f"Ошибка базы данных: {e}", None

async def get_anime_titles_by_genre(genre: str):
    try:
        conn = await aiomysql.connect(
            host='mysql-lakalut.alwaysdata.net',
            port=3306,
            user='lakalut',
            password='cfrfvjnj1201',
            db='lakalut_tbot'
        )
        async with conn.cursor() as cur:
            await cur.execute("SELECT title FROM anime WHERE genre = %s", (genre,))
            results = await cur.fetchall()
            await conn.ensure_closed()
            if results:
                titles = "\n".join([row[0] for row in results])
                return f"Аниме в жанре '{genre}':\n{titles}"
            else:
                return f"Аниме в жанре '{genre}' не найдено."
    except Exception as e:
        return f"Ошибка базы данных: {e}"

# Проверка подписки
async def is_user_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status not in ["left", "kicked"]
    except Exception:
        return False

# Клавиатуры
search_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📄 Код"), KeyboardButton(text="🎭 Жанр")],
        [KeyboardButton(text="ℹ️ Информация")]
    ],
    resize_keyboard=True
)

code_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Знаю"), KeyboardButton(text="🔍 Найти (в ТТ)")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

genre_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧙‍♂️ Фэнтэзи"), KeyboardButton(text="💖 Романтика")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

info_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

# Обработчики
@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    if await is_user_subscribed(message.from_user.id):
        await message.answer("Привет! Выберите опцию:", reply_markup=search_keyboard)
    else:
        await message.answer(
            'Для использования бота необходимо подписаться на канал. <a href="https://t.me/+kD6jJfENAXJhZjAy">тык 3&lt;</a>, после нажимите снова /start',
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )

async def check_subscription_and_respond(message: types.Message):
    if not await is_user_subscribed(message.from_user.id):
        await message.answer(
            'Для использования бота необходимо подписаться на канал. <a href="https://t.me/+kD6jJfENAXJhZjAy">тык 3&lt;</a>, после нажимите снова /start',
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )
        return False
    return True

@dp.message(lambda message: message.text == "📄 Код")
async def show_code_options(message: types.Message):
    if await check_subscription_and_respond(message):
        await message.answer("Знаете код аниме?", reply_markup=code_keyboard)

@dp.message(lambda message: message.text == "🎭 Жанр")
async def handle_genre_option(message: types.Message):
    if await check_subscription_and_respond(message):
        await message.answer("Выберите жанр:", reply_markup=genre_keyboard)

@dp.message(lambda message: message.text == "ℹ️ Информация")
async def handle_info_option(message: types.Message):
    if await check_subscription_and_respond(message):
        await message.answer("В разделе 'Информация' ничего нет.", reply_markup=info_keyboard)

@dp.message(lambda message: message.text == "🔙 Назад")
async def handle_back_to_search(message: types.Message):
    if await check_subscription_and_respond(message):
        await message.answer("Возвращаюсь в меню:", reply_markup=search_keyboard)

@dp.message(lambda message: message.text == "✅ Знаю")
async def handle_know_option(message: types.Message):
    if await check_subscription_and_respond(message):
        await message.answer("Отлично! Введите код понравившегося аниме:")

@dp.message(lambda message: message.text == "🔍 Найти (в ТТ)")
async def handle_tiktok_option(message: types.Message):
    if await check_subscription_and_respond(message):
        tiktok_url = "https://www.tiktok.com/@bbw.anime"
        await message.answer(
            f"Чтобы подобрать себе аниме по коду, перейди в мой TikTok аккаунт: {tiktok_url}\n\n"
            f"После того как найдёшь, вернись в бота и нажми ✅ Знаю, после вводи код аниме, которое тебе приглянулось :)"
        )

@dp.message(lambda message: message.text == "💖 Романтика")
async def handle_romance_genre(message: types.Message):
    if await check_subscription_and_respond(message):
        result = await get_anime_titles_by_genre("Романтика")
        await message.answer(result)

@dp.message(lambda message: message.text == "🧙‍♂️ Фэнтэзи")
async def handle_fantasy_genre(message: types.Message):
    if await check_subscription_and_respond(message):
        result = await get_anime_titles_by_genre("Фэнтэзи")
        await message.answer(result)

@dp.message(lambda message: message.text.strip().isalnum())
async def handle_anime_code(message: types.Message):
    if await check_subscription_and_respond(message):
        code = message.text.strip()
        text, image_url = await get_anime_by_code(code)
        if image_url:
            await message.answer_photo(photo=image_url, caption=text)
        else:
            await message.answer(text)

# Запуск
async def main():
    await dp.start_polling(bot)
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

if __name__ == '__main__':
    keep_alive()  # запускаем Flask-сервер в фоновом потоке
    asyncio.run(main())  # запускаем Telegram-бота


