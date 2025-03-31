# handlers/commands.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(Command("speaker"))
async def speaker_command(message: Message, state: FSMContext):
    print('Speaker')
    data = await state.get_data()
    print(data)
    if data.get("speaker"):
        await message.answer("Вы уже авторизованы как участник. Перехожу в меню участника...")
        from handlers.speaker import show_speaker_menu
        await show_speaker_menu(message, state)
    else:
        await message.answer("Вы не авторизованы как участник. Пожалуйста, нажмите /start и выберите роль 'Участник 🎤' для авторизации.")

@router.message(Command("companion"))
async def companion_command(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("teacher") and data.get("projects"):
        from handlers.chaperone import show_chaperone_menu
        await show_chaperone_menu(message, state)
    else:
        await message.answer("Вы не авторизованы как сопровождающий. Пожалуйста, нажмите /start и выберите роль 'Сопровождающий 🧑‍🏫' для авторизации.")

@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer("Для того чтобы связаться с администратором позвоните по номеру [+7 (777) 777 77-77](tel:+79991234567) доб 7777", parse_mode="Markdown")

@router.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer("Начало работы бота. Пожалуйста, выберите роль.")

@router.message(Command("reset"))
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Сбросили ваши данные для авторизации")