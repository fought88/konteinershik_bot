import os
import json

# Сохраняем GOOGLE_CREDENTIALS_JSON как файл
credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
if credentials_json:
    with open("google_credentials.json", "w", encoding="utf-8") as f:
        f.write(credentials_json)

from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from config import BOT_TOKEN, ADMIN_ID
import gspread
from datetime import datetime
import re

gc = gspread.service_account(filename="google_credentials.json")
sheet = gc.open("Konteinershik Leads").sheet1

class Form(StatesGroup):
    city = State()
    condition = State()
    type = State()
    height = State()
    urgency = State()
    phone = State()
    confirm = State()

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await message.answer("👋 Добро пожаловать! Давайте подберём вам контейнер.")
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Отправить местоположение", request_location=True)]],
        resize_keyboard=True
    )
    await message.answer("Укажите город или отправьте свою геолокацию:", reply_markup=markup)
    await state.set_state(Form.city)

@dp.message(Form.city)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Новый")], [KeyboardButton(text="Б/У")]],
        resize_keyboard=True
    )
    await message.answer("Контейнер нужен новый или Б/У?", reply_markup=markup)
    await state.set_state(Form.condition)

@dp.message(Form.condition)
async def get_condition(message: Message, state: FSMContext):
    await state.update_data(condition=message.text)
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="20 футов")], [KeyboardButton(text="40 футов")]],
        resize_keyboard=True
    )
    await message.answer("Выберите размер контейнера:", reply_markup=markup)
    await state.set_state(Form.type)

@dp.message(Form.type)
async def get_type(message: Message, state: FSMContext):
    await state.update_data(type=message.text)
    user_data = await state.get_data()
    if message.text == "20 футов":
        await state.update_data(height="2.6 м (стандарт)")
        if user_data.get("condition") == "Б/У":
            await message.answer("📸 Примеры 20-футовых Б/У контейнеров:")
            await message.answer("https://disk.yandex.ru/d/EotWlFU9n7tPFg")
            await message.answer("https://disk.yandex.ru/d/u7I05yGQu2BxOg")
        await ask_urgency(message, state)
    elif message.text == "40 футов":
        markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="2.6 м")], [KeyboardButton(text="2.9 м")]],
            resize_keyboard=True
        )
        await message.answer("Выберите высоту контейнера:", reply_markup=markup)
        await state.set_state(Form.height)

@dp.message(Form.height)
async def get_height(message: Message, state: FSMContext):
    await state.update_data(height=message.text)
    if message.text == "2.6 м":
        await message.answer("📸 Примеры 40-футовых контейнеров 2.6 м:")
        await message.answer("https://disk.yandex.ru/d/tZ6o_IU7BKvfnA")
    elif message.text == "2.9 м":
        await message.answer("📸 Примеры 40-футовых контейнеров 2.9 м:")
        await message.answer("https://disk.yandex.ru/d/LTfvgarLgdT3sA")
    await ask_urgency(message, state)

async def ask_urgency(message: Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Срочно")], [KeyboardButton(text="В течение недели")], [KeyboardButton(text="Без сроков")]],
        resize_keyboard=True
    )
    await message.answer("Когда нужно доставить контейнер?", reply_markup=markup)
    await state.set_state(Form.urgency)

@dp.message(Form.urgency)
async def get_urgency(message: Message, state: FSMContext):
    await state.update_data(urgency=message.text)
    await message.answer("Введите ваш номер телефона:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.phone)

@dp.message(Form.phone)
async def get_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not re.fullmatch(r"7\d{10}", phone):
        await message.answer("❗ Номер должен быть в формате <code>79001234567</code>", parse_mode="HTML")
        return

    await state.update_data(phone=phone)
    user_data = await state.get_data()

    summary = (
        f"<b>Проверьте данные заявки:</b>\n"
        f"Город: {user_data.get('city')}\n"
        f"Состояние: {user_data.get('condition')}\n"
        f"Тип: {user_data.get('type')}\n"
        f"Высота: {user_data.get('height')}\n"
        f"Срок: {user_data.get('urgency')}\n"
        f"Телефон: {user_data.get('phone')}"
    )

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Всё верно", callback_data="confirm_yes")],
        [InlineKeyboardButton(text="🔁 Изменить", callback_data="confirm_no")]
    ])
    await message.answer(summary, reply_markup=markup, parse_mode="HTML")
    await state.set_state(Form.confirm)

@dp.callback_query(lambda c: c.data == "confirm_yes")
async def confirm(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([
        now,
        data.get("city"), data.get("condition"), data.get("type"),
        data.get("height"), data.get("urgency"), data.get("phone")
    ])
    await callback.message.answer("✅ Заявка принята. Мы свяжемся с вами.")
    await state.clear()

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))