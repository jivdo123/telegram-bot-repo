import logging
import asyncio
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.enums import ParseMode

TOKEN = "7910570452:AAFG0WJYZ0ZdCxNFMLe5CPm-CrP8GIcaxQc"
ADMIN_GROUP_ID = -1002449074763  # Replace with actual admin group ID
YEARLY_GROUP_ID = -1002353177583  # Replace with actual yearly paid group ID
LIFETIME_GROUP_ID = -1002377614537  # Replace with actual lifetime paid group ID

DISCOUNT_CHANNELS = [
    "quizmitra", "quizmitra_rajasthan", "quizmitra_educational_news",
    "quizmitra_current_affairs", "quizmitragroup"
]

DB_HOST = "localhost"
DB_USER = "your_db_user"
DB_PASSWORD = "your_db_password"
DB_NAME = "your_db_name"

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

async def create_db():
    conn = await asyncpg.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            user_id BIGINT UNIQUE,
            username TEXT,
            plan TEXT,
            amount INT,
            discount BOOLEAN,
            joined_at TIMESTAMP DEFAULT NOW(),
            expiry_at TIMESTAMP
        )
    """)
    await conn.close()

@dp.message(Command("start"))
async def start_command(message: Message):
    welcome_text = (
        "✨ Welcome to Quiz Mitra Premium! ✨\n\n"
        "Get access to exclusive quizzes and premium content.\n\n"
        "📅 **Subscription Plans:**\n"
        "✅ Yearly – ₹99\n"
        "♾️ Lifetime – ₹299\n\n"
        "💰 **Get a 10% Discount!** Join our Quiz Mitra channels."
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Buy Now", callback_data="buy_now")]
    ])
    await message.answer(welcome_text, reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "buy_now")
async def buy_now(callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Yearly – ₹99", callback_data="yearly")],
        [InlineKeyboardButton(text="♾️ Lifetime – ₹299", callback_data="lifetime")]
    ])
    await callback_query.message.edit_text("Choose a plan:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data in ["yearly", "lifetime"])
async def subscription_choice(callback_query: CallbackQuery):
    plan = callback_query.data
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔹 Get Discount", callback_data=f"discount_{plan}")],
        [InlineKeyboardButton(text="💳 Buy Without Discount", callback_data=f"pay_{plan}")]
    ])
    await callback_query.message.edit_text("✨ Get a 10% Discount! Join Quiz Mitra channels:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("discount_"))
async def get_discount(callback_query: CallbackQuery):
    plan = callback_query.data.split("_")[1]
    channels_text = "\n".join([f"👉 [Join Here](https://t.me/{ch})" for ch in DISCOUNT_CHANNELS])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Check", callback_data=f"check_discount_{plan}")]
    ])
    await callback_query.message.edit_text(f"Join all channels to get a discount:\n\n{channels_text}", reply_markup=keyboard, disable_web_page_preview=True)

@dp.callback_query(lambda c: c.data.startswith("pay_"))
async def process_payment(callback_query: CallbackQuery):
    plan = callback_query.data.split("_")[1]
    amount = "₹99" if plan == "yearly" else "₹299"
    payment_text = (
        f"💳 Pay **{amount}** to:\n"
        "```
Rakesh Patel\n9461012613@ptsbi
```
"
        "📸 After payment, send a screenshot here."
    )
    await callback_query.message.edit_text(payment_text, parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(content_types=["photo"])
async def forward_screenshot(message: Message):
    caption = (
        f"🆕 **New Payment Screenshot** 🆕\n\n"
        f"📸 **User:** {message.from_user.full_name} (@{message.from_user.username})\n"
        f"🆔 **User ID:** `{message.from_user.id}`\n\n"
        "✅ **Admins, verify and approve using** `/approve user_id`."
    )
    await message.photo[-1].forward(ADMIN_GROUP_ID, caption=caption)

async def main():
    logging.basicConfig(level=logging.INFO)
    await create_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

