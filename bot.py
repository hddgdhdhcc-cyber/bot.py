
import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8081865468:AAGFd3r70yi29g86uctpwCg8mk2RKs1a9sA"
ADMIN_ID = 8250921212

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

users = {}  # {uid: {"queries": int, "banned": bool}}

class SearchState(StatesGroup):
    waiting = State()

class AdminAddOther(StatesGroup):
    target = State()
    amount = State()

class AdminBan(StatesGroup):
    target = State()

def get_main_kb(is_admin=False):
    kb = [
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🔍 Поиск")],
        [KeyboardButton(text="💳 Купить запросы"), KeyboardButton(text="🔐 Подписка")],
        [KeyboardButton(text="🆘 Поддержка")],
    ]
    if is_admin:
        kb.append([KeyboardButton(text="🛠 Админ")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

admin_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="➕ + себе"), KeyboardButton(text="➕ + другому")],
    [KeyboardButton(text="🚫 Бан/Разбан"), KeyboardButton(text="📊 Статистика")],
    [KeyboardButton(text="← Выход")],
], resize_keyboard=True)

@dp.message(CommandStart())
async def start(m: types.Message):
    uid = m.from_user.id
    if uid not in users:
        users[uid] = {"queries": 3, "banned": False}

    if users[uid]["banned"]:
        return await m.answer("🚫 Вы заблокированы.")

    text = (
        f"👋 Привет, {m.from_user.first_name}!\n\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"🔍 Запросов: <b>{users[uid]['queries']}</b>"
    )
    await m.answer(text, parse_mode="HTML", reply_markup=get_main_kb(uid == ADMIN_ID))

@dp.message(lambda m: m.text == "👤 Профиль")
async def profile(m: types.Message):
    uid = m.from_user.id
    u = users.get(uid, {"queries": 0, "banned": False})
    text = f"🆔 {uid}\nЗапросов: {u['queries']}\nСтатус: {'🚫 Бан' if u['banned'] else '✅ Активен'}"
    await m.answer(text)

@dp.message(lambda m: m.text == "🔍 Поиск")
async def begin_search(m: types.Message, state: FSMContext):
    uid = m.from_user.id
    if users.get(uid, {}).get("banned", False):
        return await m.answer("🚫 Вы заблокированы.")

    u = users.get(uid, {"queries": 0})

    if u["queries"] < 1:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Написать мне @YumeVibe", url="https://t.me/YumeVibe")]
        ])
        return await m.answer("🚫 Запросов нет.\nНапиши мне", reply_markup=kb)

    await state.set_state(SearchState.waiting)
    cancel_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ], resize_keyboard=True, one_time_keyboard=True)

    await m.answer(
        "🔍 Введи данные для поиска\n(телефон, ФИО, @ник, ID...)\n\n"
        f"Осталось: <b>{u['queries']}</b>",
        parse_mode="HTML",
        reply_markup=cancel_kb
    )

@dp.message(SearchState.waiting, lambda m: m.text == "❌ Отмена")
async def cancel_search(m: types.Message, state: FSMContext):
    await state.clear()
    await m.answer("Поиск отменён", reply_markup=get_main_kb(m.from_user.id == ADMIN_ID))

@dp.message(SearchState.waiting)
async def execute_search(m: types.Message, state: FSMContext):
    uid = m.from_user.id
    u = users.get(uid)

    if not u or u["queries"] < 1:
        await m.answer("Запросов не хватило.")
        await state.clear()
        return

    u["queries"] -= 1

    result = (
        "Результаты (демо):\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "ФИО: Иванов Иван Иванович\n"
        "Тел: +79123456789\n"
        "Город: Екатеринбург\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Осталось запросов: {u['queries']}</i>"
    )

    await m.answer(result, parse_mode="HTML")
    await state.clear()

@dp.message(lambda m: m.text in ("💳 Купить запросы", "🔐 Подписка", "🆘 Поддержка"))
async def to_creator(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Написать мне @YumeVibe", url="https://t.me/YumeVibe")]
    ])
    await m.answer("Напиши мне напрямую — подберу тариф и приму оплату", reply_markup=kb)

@dp.message(lambda m: m.text == "🛠 Админ" and m.from_user.id == ADMIN_ID)
async def admin_enter(m: types.Message):
    await m.answer("🛠 Админ-панель", reply_markup=admin_kb)

@dp.message(lambda m: m.text == "← Выход")
async def admin_exit(m: types.Message):
    await m.answer("Вернулись в меню", reply_markup=get_main_kb(True))

# + себе
@dp.message(lambda m: m.text == "➕ + себе" and m.from_user.id == ADMIN_ID)
async def add_self(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="5", callback_data="self_5"),
         InlineKeyboardButton(text="10", callback_data="self_10")],
        [InlineKeyboardButton(text="50", callback_data="self_50"),
         InlineKeyboardButton(text="100", callback_data="self_100")],
        [InlineKeyboardButton(text="500", callback_data="self_500"),
         InlineKeyboardButton(text="1000", callback_data="self_1000")]
    ])
    await m.answer("Сколько добавить себе?", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("self_") and c.from_user.id == ADMIN_ID)
async def process_self(c: types.CallbackQuery):
    amt = int(c.data.split("_")[1])
    users[ADMIN_ID]["queries"] += amt
    await c.message.edit_text(f"✅ +{amt} себе\nТеперь: {users[ADMIN_ID]['queries']}")
    await c.answer()

# + другому
@dp.message(lambda m: m.text == "➕ + другому" and m.from_user.id == ADMIN_ID)
async def add_other_start(m: types.Message, state: FSMContext):
    await state.set_state(AdminAddOther.target)
    await m.answer("Введи ID пользователя:")

@dp.message(AdminAddOther.target)
async def add_other_target(m: types.Message, state: FSMContext):
    try:
        tid = int(m.text)
        await state.update_data(target=tid)
        await state.set_state(AdminAddOther.amount)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="5", callback_data="other_5"),
             InlineKeyboardButton(text="10", callback_data="other_10")],
            [InlineKeyboardButton(text="50", callback_data="other_50"),
             InlineKeyboardButton(text="100", callback_data="other_100")],
            [InlineKeyboardButton(text="500", callback_data="other_500"),
             InlineKeyboardButton(text="1000", callback_data="other_1000")]
        ])
        await m.answer("Сколько добавить?", reply_markup=kb)
    except:
        await m.answer("❌ Неверный ID")

@dp.callback_query(lambda c: c.data.startswith("other_") and c.from_user.id == ADMIN_ID)
async def process_other(c: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    target = data.get("target")
    amt = int(c.data.split("_")[1])

    if target in users:
        users[target]["queries"] += amt
        await c.message.edit_text(f"✅ +{amt} пользователю {target}")
    else:
        await c.message.edit_text(f"Пользователь {target} не найден.")
    await state.clear()
    await c.answer()

# Бан/Разбан
@dp.message(lambda m: m.text == "🚫 Бан/Разбан" and m.from_user.id == ADMIN_ID)
async def ban_start(m: types.Message, state: FSMContext):
    await state.set_state(AdminBan.target)
    await m.answer("Введи ID пользователя:")

@dp.message(AdminBan.target)
async def process_ban(m: types.Message, state: FSMContext):
    try:
        tid = int(m.text)
        if tid in users:
            users[tid]["banned"] = not users[tid]["banned"]
            action = "заблокирован" if users[tid]["banned"] else "разблокирован"
            await m.answer(f"Пользователь {tid} {action}")
        else:
            await m.answer("Пользователь не найден.")
        await state.clear()
    except:
        await m.answer("❌ Неверный ID")

# Статистика
@dp.message(lambda m: m.text == "📊 Статистика" and m.from_user.id == ADMIN_ID)
async def stats(m: types.Message):
    total = len(users)
    banned = sum(1 for v in users.values() if v["banned"])
    total_q = sum(v["queries"] for v in users.values())
    text = f"Пользователей: {total}\nЗабанено: {banned}\nЗапросов всего: {total_q}"
    await m.answer(text)

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
