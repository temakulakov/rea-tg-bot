# handlers/start.py
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def start_command(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Участник 🎤", callback_data="role_speaker")],
        [InlineKeyboardButton(text="Сопровождающий 🧑‍🏫", callback_data="role_chaperone")]
    ])
    await message.answer("👋 Привет! На конференции ты присутствуешь как:", reply_markup=kb)
