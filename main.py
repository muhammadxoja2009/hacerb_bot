import logging
import config
from aiogram import Bot, Dispatcher, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile, Message
import json
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

USER_DATA = {}
EARTH_VIEWS_FILE = os.path.join("data", "earth_views.json")

with open(EARTH_VIEWS_FILE, "r", encoding="utf-8") as file:
    EARTH_VIEWS = json.load(file)

if not os.path.exists("data/users.json"):
    with open("data/users.json", "w") as file:
        json.dump({}, file)

def load_users():
    global USER_DATA
    with open("data/users.json", "r") as file:
        try:
            USER_DATA = json.load(file)
        except json.JSONDecodeError:
            USER_DATA = {}
            save_users()

def save_users():
    with open("data/users.json", "w") as file:
        json.dump(USER_DATA, file, indent=4)

def check_user(user_id: int, message: Message):
    joined_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    load_users()

    if str(user_id) in USER_DATA:
        print("User exists")
        return False

    USER_DATA[str(user_id)] = {
        "user_id": user_id,
        "first_name": message.from_user.first_name,
        "username": message.from_user.username,
        "joined_date": joined_date
    }

    save_users()
    return True

@dp.message_handler(commands=['start'])
async def welcome(message: Message):
    user_id = message.from_user.id
    load_users()

    joined = check_user(user_id, message)

    if joined:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"👤 *Yangi foydalanuvchi qo‘shildi!*
"
                 f"ID: `{user_id}`
"
                 f"Username: @{message.from_user.username}
"
                 f"Ism: {message.from_user.first_name}",
            parse_mode="Markdown"
        )

    await message.answer(
        f"👋 Salom, *{message.from_user.first_name}!* 
"
        f"Quyidagi bo‘limlardan birini tanlang:",
        parse_mode="Markdown",
        reply_markup=home_keyboard()
    )

def home_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🌍 Yer panoramalari", callback_data="earth_views"),
        InlineKeyboardButton("📚 Biz haqimizda", callback_data="about")
    )
    return keyboard

@dp.callback_query_handler(lambda call: True)
async def callback_handler(call):
    if call.data == "home":
        await call.message.edit_text(
            "🏠 Bosh sahifa", reply_markup=home_keyboard()
        )

    elif call.data == "earth_views":
        await call.message.edit_text(
            "🌍 Qaysi panoramani ko‘rmoqchisiz?",
            reply_markup=earth_views_keyboard()
        )

    elif call.data.startswith("earth_"):
        index = int(call.data.split("_")[1])
        view = EARTH_VIEWS[index]

        await call.message.answer_photo(
            photo=view["image"],
            caption=f"🌍 {view['name']}

{view['description']}"
        )

    elif call.data == "about":
        await call.message.edit_text(
            "📚 *Biz haqimizda*

Bu bot yer panoramalarini ko‘rsatadi.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("🏠 Bosh sahifa", callback_data="home")
            )
        )

def earth_views_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    for i, view in enumerate(EARTH_VIEWS):
        keyboard.add(InlineKeyboardButton(view["name"], callback_data=f"earth_{i}"))
    keyboard.add(InlineKeyboardButton("🏠 Bosh sahifa", callback_data="home"))
    return keyboard

if __name__ == "__main__":
    load_users()
    executor.start_polling(dp)
