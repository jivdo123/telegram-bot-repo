import logging
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# Telegram API Token
TOKEN = "7910570452:AAFG0WJYZ0ZdCxNFMLe5CPm-CrP8GIcaxQc"
ADMIN_GROUP_ID = -1002449074763  # Replace with actual admin group ID
YEARLY_GROUP_ID = -1002353177583  # Replace with actual yearly paid group ID
LIFETIME_GROUP_ID = -1002377614537  # Replace with actual lifetime paid group ID

# Discount Channels
DISCOUNT_CHANNELS = [
    "quizmitra", "quizmitra_rajasthan", "quizmitra_educational_news",
    "quizmitra_current_affairs", "quizmitragroup"
]

# PostgreSQL Credentials
DB_HOST = "localhost"
DB_USER = "your_db_user"
DB_PASSWORD = "your_db_password"
DB_NAME = "your_db_name"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

# Database Connection
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


# --- Start Command ---
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    welcome_text = (
        "✨ **Welcome to Quiz Mitra Premium!** ✨\n\n"
        "Get access to **exclusive quizzes** and premium content.\n\n"
        "**Subscription Plans:**\n"
        "📅 **Yearly** – ₹99\n"
        "♾️ **Lifetime** – ₹299\n\n"
        "🔹 **Join for a 10% Discount!** If you join our Quiz Mitra channels, you’ll get a special discount."
    )

    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("Buy Now", callback_data="buy_now"))
    await message.answer(welcome_text, reply_markup=keyboard)


# --- Subscription Plan Selection ---
@dp.callback_query_handler(lambda c: c.data == "buy_now")
async def select_plan(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("📅 Yearly – ₹99", callback_data="yearly"),
        InlineKeyboardButton("♾️ Lifetime – ₹299", callback_data="lifetime")
    )
    await callback_query.message.edit_text("Choose a plan:", reply_markup=keyboard)


# --- Discount Offer ---
@dp.callback_query_handler(lambda c: c.data in ["yearly", "lifetime"])
async def discount_offer(callback_query: types.CallbackQuery):
    plan = callback_query.data
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🔹 Get Discount", callback_data=f"get_discount_{plan}"),
        InlineKeyboardButton("💳 Buy Without Discount", callback_data=f"pay_{plan}")
    )
    await callback_query.message.edit_text(
        "✨ **Get a 10% Discount!**\n\nJoin our **Quiz Mitra** channels and get a discount.\n\n"
        "Click below to proceed.",
        reply_markup=keyboard
    )


# --- Show Discount Channels ---
@dp.callback_query_handler(lambda c: c.data.startswith("get_discount"))
async def show_channels(callback_query: types.CallbackQuery):
    plan = callback_query.data.split("_")[-1]
    channels_text = "\n".join([f"👉 [Join Here](https://t.me/{ch})" for ch in DISCOUNT_CHANNELS])
    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Check", callback_data=f"check_discount_{plan}"))
    
    await callback_query.message.edit_text(
        f"**Join all channels below to get a 10% discount:**\n\n{channels_text}\n\n"
        "**You must join all channels to qualify.** Click 'Check' after joining.",
        reply_markup=keyboard,
        disable_web_page_preview=True
    )


# --- Verify Channel Join Status ---
@dp.callback_query_handler(lambda c: c.data.startswith("check_discount"))
async def check_channels(callback_query: types.CallbackQuery):
    plan = callback_query.data.split("_")[-1]
    user_id = callback_query.from_user.id

    for channel in DISCOUNT_CHANNELS:
        chat_member = await bot.get_chat_member(f"@{channel}", user_id)
        if chat_member.status not in ["member", "administrator", "creator"]:
            await callback_query.message.answer("❌ You haven't joined all required channels. Please join and try again.")
            return

    price = 90 if plan == "yearly" else 270
    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Paid? Send Screenshot", callback_data="send_screenshot"))

    await callback_query.message.edit_text(
        f"✅ **Discount Applied!**\n\n"
        f"💳 Pay **₹{price}** to:\n"
        f"```\nRakesh Patel\n9461012613@ptsbi\n```\n"
        "📸 After payment, send a screenshot here.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# --- Payment Without Discount ---
@dp.callback_query_handler(lambda c: c.data.startswith("pay_"))
async def pay_without_discount(callback_query: types.CallbackQuery):
    plan = callback_query.data.split("_")[-1]
    price = 99 if plan == "yearly" else 299
    keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Paid? Send Screenshot", callback_data="send_screenshot"))

    await callback_query.message.edit_text(
        f"💳 Pay **₹{price}** to:\n"
        f"```\nRakesh Patel\n9461012613@ptsbi\n```\n"
        "📸 After payment, send a screenshot here.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# --- Forward Payment Screenshot to Admin Group ---
@dp.message_handler(content_types=["photo"])
async def forward_screenshot(message: types.Message):
    caption = (
        f"🆕 **New Payment Screenshot** 🆕\n\n"
        f"👤 **User:** {message.from_user.full_name} (@{message.from_user.username})\n"
        f"🆔 **User ID:** `{message.from_user.id}`\n\n"
        "✅ **Admins, verify and approve using** `/approve user_id`."
    )
    await message.photo[-1].forward(ADMIN_GROUP_ID, caption=caption)


# --- Manual Admin Approval ---
@dp.message_handler(commands=["approve"])
async def approve_user(message: types.Message):
    if not message.reply_to_message:
        await message.reply("❌ Reply to the payment screenshot with `/approve user_id`.")
        return

    user_id = int(message.text.split()[1])
    plan = "Yearly" if "₹90" in message.reply_to_message.caption else "Lifetime"
    group_id = YEARLY_GROUP_ID if plan == "Yearly" else LIFETIME_GROUP_ID

    await bot.add_chat_members(group_id, user_id)
    await bot.send_message(user_id, f"🎉 **Congratulations!** You've been added to the {plan} paid group!")

executor.start_polling(dp, skip_updates=True)
