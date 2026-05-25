import asyncio
import json
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
    CallbackQuery,
    Message
)
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ================= НАСТРОЙКИ =================

TOKEN = "8930236706:AAG9Gw5SFRhSHdG_SLk2YKM9hO5zTOVNKGg"
ADMIN_ID = 6770764111

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================= ФАЙЛЫ =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CATALOG_FILE = os.path.join(BASE_DIR, "catalog.json")
ORDERS_FILE = os.path.join(BASE_DIR, "orders.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")

PHOTOS_DIR = os.path.join(BASE_DIR, "photos")

os.makedirs(PHOTOS_DIR, exist_ok=True)

# ================= СОЗДАНИЕ ФАЙЛОВ =================

if not os.path.exists(CATALOG_FILE):
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "2000_5000": [],
            "5000_10000": [],
            "10000_20000": [],
            "10000_100000": []
        }, f, ensure_ascii=False, indent=4)

if not os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)

# ================= ФУНКЦИИ =================

def load_catalog():
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_catalog(data):
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_orders():
    with open(ORDERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_orders(data):
    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ================= FSM =================

class AddFlower(StatesGroup):
    category = State()
    name = State()
    price = State()
    photo = State()

class Broadcast(StatesGroup):
    text = State()

class DeleteFlower(StatesGroup):
    number = State()

class ReplyUser(StatesGroup):
    user_id = State()
    text = State()

class ChangePrice(StatesGroup):
    number = State()
    new_price = State()

# ================= КНОПКИ =================

def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💐 Букеты 2000-5000₽",
                    callback_data="cat|2000_5000"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🌸 Букеты 5000-10000₽",
                    callback_data="cat|5000_10000"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🌹 Букеты 10000-20000₽",
                    callback_data="cat|10000_20000"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👑 VIP букеты",
                    callback_data="cat|vip"
                )
            ]
        ]
    )

def admin_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить букет", callback_data="admin_add")],
            [InlineKeyboardButton(text="💰 Изменить цену", callback_data="admin_price")],
            [InlineKeyboardButton(text="✉️ Ответить", callback_data="admin_reply")],
            [InlineKeyboardButton(text="❌ Удалить букет", callback_data="admin_delete")],
            [InlineKeyboardButton(text="📦 Заявки", callback_data="admin_orders")],
            [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")]
        ]
    )

# ================= СТАРТ =================

@dp.message(Command("start"))
async def start_handler(message: Message):

    users = load_users()

    if message.from_user.id not in [u["id"] for u in users]:

        users.append({
            "id": message.from_user.id,
            "name": message.from_user.first_name,
            "username": message.from_user.username
        })

        save_users(users)

        username = (
            f"@{message.from_user.username}"
            if message.from_user.username
            else "Без username"
        )

        await bot.send_message(
            ADMIN_ID,
            f"🆕 Новый пользователь\n\n"
            f"👤 Имя: {message.from_user.first_name}\n"
            f"🔗 Username: {username}\n"
            f"🆔 ID: {message.from_user.id}"
        )

    await message.answer(
        "🌸 Добро пожаловать в магазин цветов!",
        reply_markup=main_menu()
    )

# ================= АДМИН =================

@dp.message(Command("admin"))
async def admin_panel(message: Message):

    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Нет доступа")
        return

    await message.answer(
        "🔐 Админ панель",
        reply_markup=admin_menu()
    )

# ================= ДОБАВЛЕНИЕ =================

@dp.callback_query(F.data == "admin_add")
async def add_start(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer(
        "Введите номер категории:\n\n"
        "1. 2000_5000\n"
        "2. 5000_10000\n"
        "3. 10000_20000\n"
        "4. 20000_100000"
    )

    await state.set_state(AddFlower.category)

    await callback.answer()

@dp.message(AddFlower.category)
async def add_category(message: Message, state: FSMContext):

    categories = {
        "1": "2000_5000",
        "2": "5000_10000",
        "3": "10000_20000",
        "4": "20000_100000"
    }

    if message.text not in categories:
        await message.answer("❌ Введите цифру от 1 до 4")
        return

    await state.update_data(category=categories[message.text])

    await message.answer("Введите название букета")

    await state.set_state(AddFlower.name)

@dp.message(AddFlower.name)
async def add_name(message: Message, state: FSMContext):

    await state.update_data(name=message.text)

    await message.answer("Введите цену")

    await state.set_state(AddFlower.price)

@dp.message(AddFlower.price)
async def add_price(message: Message, state: FSMContext):

    await state.update_data(price=message.text)

    await message.answer("Отправьте фото букета")

    await state.set_state(AddFlower.photo)

@dp.message(AddFlower.photo)
async def add_photo(message: Message, state: FSMContext):

    if not message.photo:
        await message.answer("Нужно отправить фото")
        return

    data = await state.get_data()

    catalog = load_catalog()

    category = data["category"]
    name = data["name"]
    price = data["price"]

    file = await bot.get_file(message.photo[-1].file_id)

    filename = f"{name}.jpg"

    file_path = os.path.join(PHOTOS_DIR, filename)

    await bot.download_file(file.file_path, file_path)

    catalog[category].append({
        "name": name,
        "price": price,
        "photo": filename
    })

    save_catalog(catalog)

    await message.answer("✅ Букет добавлен")

    await state.clear()

# ================= ПРОСМОТР БУКЕТОВ =================

def flower_keyboard(category, index, total):

    buttons = []

    row = []

    if index > 0:
        row.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"view|{category}|{index - 1}"
            )
        )

    row.append(
        InlineKeyboardButton(
            text="🛒 Заказать",
            callback_data=f"order|{category}|{index}"
        )
    )

    if index < total - 1:
        row.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"view|{category}|{index + 1}"
            )
        )

    buttons.append(row)

    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="home"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.callback_query(lambda c: c.data.startswith("cat|"))
async def open_category(callback: CallbackQuery):

    _, category = callback.data.split("|")

    catalog = load_catalog()

    flowers = catalog[category]

    if not flowers:
        await callback.message.answer("Пока нет букетов")
        await callback.answer()
        return

    flower = flowers[0]

    photo_path = os.path.join(PHOTOS_DIR, flower["photo"])

    caption = (
        f"🌸 {flower['name']}\n\n"
        f"💰 Цена: {flower['price']}₽"
    )

    kb = flower_keyboard(category, 0, len(flowers))

    await callback.message.answer_photo(
        FSInputFile(photo_path),
        caption=caption,
        reply_markup=kb
    )

    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("view|"))
async def view_flower(callback: CallbackQuery):

    _, category, index = callback.data.split("|")

    index = int(index)

    catalog = load_catalog()

    flowers = catalog[category]

    flower = flowers[index]

    photo_path = os.path.join(PHOTOS_DIR, flower["photo"])

    caption = (
        f"🌸 {flower['name']}\n\n"
        f"💰 Цена: {flower['price']}₽"
    )

    kb = flower_keyboard(category, index, len(flowers))

    media = types.InputMediaPhoto(
        media=FSInputFile(photo_path),
        caption=caption
    )

    await callback.message.edit_media(
        media=media,
        reply_markup=kb
    )

    await callback.answer()

# ================= ЗАКАЗ =================

@dp.callback_query(lambda c: c.data.startswith("order|"))
async def make_order(callback: CallbackQuery):

    _, category, index = callback.data.split("|")

    index = int(index)

    catalog = load_catalog()

    flower = catalog[category][index]

    user = callback.from_user

    orders = load_orders()

    orders.append({
        "user_id": user.id,
        "name": user.first_name,
        "username": user.username,
        "flower": flower["name"],
        "price": flower["price"]
    })

    save_orders(orders)

    username = (
        f"@{user.username}"
        if user.username
        else "Без username"
    )

    text = (
        "🛒 НОВЫЙ ЗАКАЗ\n\n"
        f"👤 Имя: {user.first_name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: {user.id}\n\n"
        f"💐 Букет: {flower['name']}\n"
        f"💰 Цена: {flower['price']}₽"
    )

    await bot.send_message(ADMIN_ID, text)

    await callback.message.answer(
        "✅ Заявка отправлена!"
    )

    await callback.answer()

# ================= ГЛАВНОЕ МЕНЮ =================

@dp.callback_query(F.data == "home")
async def home(callback: CallbackQuery):

    await callback.message.answer(
        "🏠 Главное меню",
        reply_markup=main_menu()
    )

    await callback.answer()

# ================= УДАЛЕНИЕ =================

@dp.callback_query(F.data == "admin_delete")
async def delete_list(callback: CallbackQuery, state: FSMContext):

    catalog = load_catalog()

    text = "❌ Введите номер букета для удаления:\n\n"

    items = []

    counter = 0

    for category in catalog:
        for flower in catalog[category]:
            counter += 1

            items.append((category, flower["name"]))

            text += f"{counter}. {flower['name']} ({category})\n"

    with open("delete_map.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False)

    await callback.message.answer(text)

    await state.set_state(DeleteFlower.number)

    await callback.answer()

# ================= ЗАЯВКИ =================

@dp.message(DeleteFlower.number)
async def delete_flower(message: Message, state: FSMContext):

    if not message.text.isdigit():
        await message.answer("Введите число")
        return

    number = int(message.text)

    with open("delete_map.json", "r", encoding="utf-8") as f:
        items = json.load(f)

    if number < 1 or number > len(items):
        await message.answer("❌ Неверный номер")
        return

    category, flower_name = items[number - 1]

    catalog = load_catalog()

    flower_to_delete = None

    for flower in catalog[category]:

        if flower["name"] == flower_name:
            flower_to_delete = flower
            break

    if flower_to_delete:

        catalog[category].remove(flower_to_delete)

        save_catalog(catalog)

        await message.answer("✅ Букет удалён")

    else:

        await message.answer("❌ Букет не найден")

    await state.clear()
@dp.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery):

    orders = load_orders()

    if not orders:
        await callback.message.answer("📦 Заявок пока нет")
        await callback.answer()
        return

    text = "📦 ЗАЯВКИ\n\n"

    for order in orders:

        username = (
            f"@{order['username']}"
            if order["username"]
            else "Без username"
        )

        text += (
    f"👤 {order['name']}\n"
    f"{username}\n"
    f"🆔 {order['user_id']}\n"
    f"💐 {order['flower']}\n"
    f"💰 {order['price']}₽\n\n"
)

    await callback.message.answer(text)

    await callback.answer()

# ================= ПОЛЬЗОВАТЕЛИ =================

@dp.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):

    users = load_users()

    await callback.message.answer(
        f"👥 Пользователей: {len(users)}"
    )

    await callback.answer()

# ================= РАССЫЛКА =================

@dp.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer(
        "Введите сообщение для рассылки"
    )

    await state.set_state(Broadcast.text)

    await callback.answer()

@dp.message(Broadcast.text)
async def broadcast_send(message: Message, state: FSMContext):

    users = load_users()

    sent = 0

    for user in users:
        try:
            await bot.send_message(user["id"], message.text)
            sent += 1
        except:
            pass

    await message.answer(
        f"✅ Отправлено: {sent}"
    )

    await state.clear()

# ================= ИЗМЕНЕНИЕ ЦЕНЫ =================

@dp.callback_query(F.data == "admin_price")
async def change_price_start(callback: CallbackQuery, state: FSMContext):

    catalog = load_catalog()

    text = "💰 Введите номер букета:\n\n"

    items = []

    counter = 0

    for category in catalog:
        for flower in catalog[category]:

            counter += 1

            items.append((category, flower["name"]))

            text += (
                f"{counter}. "
                f"{flower['name']} "
                f"({flower['price']}₽)\n"
            )

    with open("price_map.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False)

    await callback.message.answer(text)

    await state.set_state(ChangePrice.number)

    await callback.answer()

@dp.message(ChangePrice.number)
async def change_price_number(message: Message, state: FSMContext):

    try:
        number = int(message.text)
    except:
        await message.answer("Введите номер")
        return

    await state.update_data(number=number)

    await message.answer("Введите новую цену")

    await state.set_state(ChangePrice.new_price)

@dp.message(ChangePrice.new_price)
async def change_price_save(message: Message, state: FSMContext):

    data = await state.get_data()

    number = data["number"]

    with open("price_map.json", "r", encoding="utf-8") as f:
        items = json.load(f)

    if number < 1 or number > len(items):
        await message.answer("Неверный номер")
        return

    category, flower_name = items[number - 1]

    catalog = load_catalog()

    for flower in catalog[category]:

        if flower["name"] == flower_name:

            flower["price"] = message.text

            break

    save_catalog(catalog)

    await message.answer("✅ Цена изменена")

    await state.clear()
# ================= ОТВЕТ ПОЛЬЗОВАТЕЛЮ =================

@dp.callback_query(F.data == "admin_reply")
async def reply_start(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer(
        "Введите ID пользователя"
    )

    await state.set_state(ReplyUser.user_id)

    await callback.answer()

@dp.message(ReplyUser.user_id)
async def reply_get_id(message: Message, state: FSMContext):

    await state.update_data(user_id=message.text)

    await message.answer(
        "Введите сообщение пользователю"
    )

    await state.set_state(ReplyUser.text)

@dp.message(ReplyUser.text)
async def reply_send(message: Message, state: FSMContext):

    data = await state.get_data()

    user_id = data["user_id"]

    try:

        await bot.send_message(
            int(user_id),
            f"💬 Сообщение от администратора:\n\n{message.text}"
        )

        await message.answer("✅ Сообщение отправлено")

    except:

        await message.answer("❌ Ошибка отправки")

    await state.clear()
# ================= ЗАПУСК =================

if __name__ == "__main__":
    print("Бот запущен...")
    asyncio.run(dp.start_polling(bot))