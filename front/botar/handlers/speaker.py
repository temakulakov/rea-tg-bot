# handlers/speaker.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from states.states import SpeakerState
from utils.validators import is_valid_full_name, normalize_name
from services import api_client
from lang import yes, no, cancel, back
from utils.validators import  format_datetime
import datetime

router = Router()

async def show_speaker_menu(message: Message, state: FSMContext):
    data = await state.get_data()
    speaker = data.get("speaker", {})
    school_name = speaker.get("school_name", "не указана")
    main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Моя конференция 📅", callback_data="show_conference")],
        [InlineKeyboardButton(text="Мастер-классы 📐", callback_data="show_workshops")]
    ])
    await message.answer(f"🎉 **Добро пожаловать, {speaker.get('name', '')}**! Школа: *{school_name}* 🏫", parse_mode="Markdown")
    await message.answer("Главное меню участника 🎤", reply_markup=main_menu_kb)

@router.callback_query(F.data == "role_speaker")
async def start_speaker(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора роли спикера."""
    await callback.answer()  # Подтверждаем callback
    data = await state.get_data()
    if data.get("speaker"):
        # Если данные уже есть – спрашиваем подтверждение через inline-клавиатуру
        print(data["speaker"])
        await state.set_state(SpeakerState.confirm_identity)
        await callback.message.edit_text(
            f"👋 Привет! Это ты? {data['speaker'].get('name', '')} {data['speaker'].get('second_name', '@')}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=yes, callback_data="speaker_yes"),
                 InlineKeyboardButton(text=no, callback_data="speaker_no")]
            ])
        )
    else:
        # Если данных нет, удаляем исходное сообщение с inline-клавиатурой
        await callback.message.delete()
        # Устанавливаем состояние для ввода ФИО и отправляем одно сообщение с reply-клавиатурой "Отмена"
        await state.set_state(SpeakerState.choosing_name)
        cancel_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отмена")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await callback.message.answer("Введи своё полное имя ✏️:", reply_markup=cancel_kb, one_time_keyboard=True)

@router.message(Command("start"))
async def start_command(message: Message):
    """Обработчик команды /start."""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Участник 🎤", callback_data="role_speaker")],
        [InlineKeyboardButton(text="Сопровождающий 🎓", callback_data="role_chaperone")]
    ])
    await message.answer("👋 Привет! На конференции ты присутствуешь как:", reply_markup=kb)

@router.message(SpeakerState.choosing_name)
async def receive_full_name(message: Message, state: FSMContext):
    """Получение ФИО спикера с проверкой."""
    full_name = message.text.strip()
    if full_name.lower() == "отмена":
        await message.answer("Отмена. Запусти /start снова.")
        await state.clear()
        return
    if not is_valid_full_name(full_name):
        await message.answer("😵‍💫 Ошибка: имя должно состоять из двух слов и не содержать английских букв. Попробуй ещё раз:")
        return
    query = normalize_name(full_name)
    speaker_data = await api_client.search_speaker(query)
    print(speaker_data)
    if speaker_data is None:
        await message.answer("👀 Участник не найден. Попробуй ещё раз в формате (Фамилия Имя Отчество) или нажми Отмена.")
        return
    
    # Сохраняем список и СБРАСЫВАЕМ индекс в 0
    await state.update_data(
        speakers=speaker_data['data'],
        current_speaker_index=0
    )
    
    await show_next_speaker(message, state)  # Запускаем показ первого спикера
    # await state.update_data(speaker=speaker_data)
    # await state.update_data(authorized_role="speaker")
    # await state.set_state(SpeakerState.confirm_identity)
    # buttons = [
    #     [InlineKeyboardButton(text="Да", callback_data="speaker_yes"),
    #      InlineKeyboardButton(text="Нет", callback_data="speaker_no")]
    # ]
    # import pprint
    # pprint.pprint(speaker_data)
    
    # for speaker in speaker_data['data']:
    #     response_text = (
    #         f"Найден спикер:\n"
    #         f"Имя: {speaker.get('name', 'не указано')}\n"
    #         f"Фамилия: {speaker.get('second_name', 'не указано')}\n"
    #         f"Проект: {speaker.get('project_name', 'не указан')}\n"
    #         f"Формат проекта: {speaker.get('project_format', 'не указан')}\n"
    #         f"Номер слота: {speaker.get('project_slot', 'не указан')}\n"
    #         f"Класс: {speaker.get('school_class', 'не указан')}\n"
    #         f"Школа: {speaker.get('school_name', 'не указана')}\n"
    #         f"Это ты?"
    #     )
        
    #     q = await message.answer(response_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    #     print("APISBFPUIAS: ", q)
    #     print("XUYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY")

@router.callback_query(StateFilter(SpeakerState.confirm_identity), F.data == "speaker_yes")
async def confirm_speaker_yes(callback: CallbackQuery, state: FSMContext):
    """Подтверждение данных спикера."""
    await callback.answer()
    
    data = await state.get_data()
    speakers = data.get("speakers", [])
    current_index = data.get("current_speaker_index", 0)
    
    if current_index >= len(speakers):
        await callback.answer("Ошибка данных")
        return
    
    # Сохраняем ВЫБРАННОГО спикера
    selected_speaker = speakers[current_index]
    await state.update_data(
        speaker=selected_speaker,
        authorized_role="speaker"
    )
    
    await state.set_state(SpeakerState.main_menu)
    
    main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Моя конференция 📅", callback_data="show_conference")],
        [InlineKeyboardButton(text="Мастер-классы 📐", callback_data="show_workshops")]
    ])
    
    await callback.message.edit_text(
        f"👏 Отлично, {selected_speaker.get('name', '')}! Твои данные сохранены ✅", 
        reply_markup=main_menu_kb
    )

async def show_next_speaker(message: Message, state: FSMContext):
    """Показывает следующего спикера из списка"""
    data = await state.get_data()
    speakers = data.get("speakers", [])
    current_index = data.get("current_speaker_index", 0)
    
    # Если достигли конца списка
    if current_index >= len(speakers):
        await message.answer("👀 Больше вариантов нет. Введи имя снова в формате (Фамилия Имя Отчество)")
        await state.set_state(SpeakerState.choosing_name)
        return
    
    # Получаем текущего спикера
    current_speaker = speakers[current_index]
    
    # Формируем сообщение
    response_text = (
        f"✨ Найден участник:\n"
        f"""👤 *ФИО:* {current_speaker.get('name', 'не указано')}\t 
        {current_speaker.get('second_name', 'не указано')}\t 
        {current_speaker.get('father_name', '')}\n"""
        f"📝 *Проект:*  {current_speaker.get('project_name', 'не указан')}\n"
        f"🎤 *Формат проекта:* {current_speaker.get('project_format', 'не указан')}\n"
        f"🔢 *Номер аудитории:* {int(float(current_speaker.get('project_slot', 'не указан')))}\n"
        f"👥 *Класс:* {current_speaker.get('school_class', 'не указан')}\n"
        f"🏫 *Школа:* {current_speaker.get('school_name', 'не указана')}\n"
        f"🕐 *Время начала:* {format_datetime(current_speaker.get('project_datetime_start', 'не указана'))}\n"
        # f"🕕 *Время окончания:* {format_datetime(current_speaker.get('project_datetime_end', 'не указана'))}\n"
        f"⏰ **Время:** {format_datetime(current_speaker.get('project_datetime_start', 'не указано'))} — {datetime.datetime.fromisoformat(current_speaker.get('project_datetime_end', 'не указано')).strftime("%H:%M")}\n"
        f"Это ты?"
    )
    
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=yes, callback_data="speaker_yes"),
         InlineKeyboardButton(text=no, callback_data="speaker_no")]
    ])
    
    await message.answer(response_text, reply_markup=buttons, parse_mode="Markdown",)
    await state.set_state(SpeakerState.confirm_identity)


@router.callback_query(StateFilter(SpeakerState.confirm_identity), F.data == "speaker_no")
async def confirm_speaker_no(callback: CallbackQuery, state: FSMContext):
    """Обработка кнопки 'Нет'"""
    await callback.answer()
    
    data = await state.get_data()
    current_index = data.get("current_speaker_index", 0)
    speakers = data.get("speakers", [])
    
    # Увеличиваем индекс
    new_index = current_index + 1
    
    if new_index >= len(speakers):
        # Если это был последний спикер
        await callback.message.answer("❌ Подходящие варианты закончились. Введи имя снова в формате (Фамилия Имя Отчество)")
        await state.set_state(SpeakerState.choosing_name)
    else:
        # Обновляем индекс и показываем следующего
        await state.update_data(current_speaker_index=new_index)
        await callback.message.delete()  # Удаляем предыдущее сообщение
        await show_next_speaker(callback.message, state)  # Показываем следующего

@router.callback_query(F.data == "show_conference")
async def inline_show_conference(callback: CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки 'Моя конференция' из inline-меню."""
    await callback.answer()
    await show_conference(callback.message, state)

@router.message(SpeakerState.main_menu, F.text == "Моя конференция 📅")
async def show_conference(message: Message, state: FSMContext):
    """Отображает данные конференции спикера с inline-клавиатурой 'Назад'."""
    data = await state.get_data()
    speaker = data.get("speaker")
    if not speaker:
        await message.answer("👀 Нет данных участника. Начни с /start.")
        await state.clear()
        return
    info_text = (
        f"Твоя конференция:\n"
        f"👤 *Имя:* {speaker.get('name', '')}\n"
        f"📝 *Проект:* {speaker.get('project_name', 'нет данных')}\n"
        f"🎤 *Формат проекта:* {speaker.get('project_format', 'не указан')}\n"
        f"🔢 *Номер аудитории:* {int(float(speaker.get('project_slot', 'не указан')))}\n"
        f"👥 *Класс:* {speaker.get('school_class', 'не указан')}\n"
        f"🏫 *Школа:* {speaker.get('school_name', 'не указана')}\n"
        f"🕐 *Время:* {speaker.get('project_time', 'уточняется')}\n"
        f"⏰ **Время:** {format_datetime(speaker.get('project_datetime_start', 'не указано'))} — {datetime.datetime.fromisoformat(speaker.get('project_datetime_end', 'не указано')).strftime("%H:%M")}\n"
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=back, callback_data="conference_back")]
    ])
    img_url = speaker.get("image_url")
    if img_url:
        try:
            await message.answer_photo(photo=img_url, caption=info_text, parse_mode="Markdown", reply_markup=back_kb)
        except Exception:
            await message.answer(info_text + "\n*(Изображение не загрузилось)*", parse_mode="Markdown", reply_markup=back_kb)
    else:
        await message.answer(info_text, parse_mode="Markdown", reply_markup=back_kb)

@router.callback_query(F.data == "conference_back")
async def conference_back(callback: CallbackQuery, state: FSMContext):
    """Обработка кнопки 'Назад' – возвращает пользователя в главное меню спикера, убирая изображение, если оно есть."""
    await callback.answer()
    main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Моя конференция 📅", callback_data="show_conference")],
        [InlineKeyboardButton(text="Мастер-классы 📐", callback_data="show_workshops")]
    ])
    # Если сообщение содержит фото, удаляем его и отправляем новое сообщение
    if callback.message.photo:
        # await callback.message.delete()
        await callback.message.answer("Главное меню участника:", reply_markup=main_menu_kb)
    # Если в сообщении есть текст, редактируем его
    elif callback.message.text:
        await callback.message.edit_text("Главное меню участника 🎤", reply_markup=main_menu_kb)
    # Если сообщение имеет caption (например, фото с подписью), редактируем caption
    elif callback.message.caption:
        await callback.message.edit_caption("Главное меню участника 🎤", reply_markup=main_menu_kb)
    else:
        await callback.message.answer("Главное меню участника 🎤", reply_markup=main_menu_kb)