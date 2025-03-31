# handlers/workshops.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from services import api_client
from datetime import datetime, date
from lang import back
from utils.validators import format_datetime, months

router = Router()  # Router for workshop-related handlers

# Словарь для перевода дней недели
DAYS_RU = {
    "Monday": "Понедельник",
    "Tuesday": "Вторник",
    "Wednesday": "Среда",
    "Thursday": "Четверг",
    "Friday": "Пятница",
    "Saturday": "Суббота",
    "Sunday": "Воскресенье"
}

@router.message(F.text == "Мастер-классы 📐")
async def list_workshop_days(message: Message, state: FSMContext):
    """Показывает доступные будущие дни мастер-классов с указанием дня недели."""
    # workshops = []
    try:
        workshops = await api_client.get_workshops()
    except api_client.ApiError as e:
        await message.answer(f"Не удалось получить список мастер-классов: {e}")
        return
    if not workshops:
        await message.answer("Нет доступных мастер-классов.")
        return
    # Фильтруем события, оставляем только будущие
    today = datetime.today().date()
    workshops_by_date = {}
    import pprint
    pprint.pprint(workshops)
    for event in workshops:
        # Используем ключ 'data' из ответа
        print(event)
        date_str = event.get('data')
        if not date_str:
            continue
        try:
            date_obj = datetime.fromisoformat(date_str).date()
        except Exception:
            continue
        if date_obj < today:
            continue  # пропускаем прошедшие события
        workshops_by_date.setdefault(date_obj, []).append(event)
    if not workshops_by_date:
        await message.answer("Нет предстоящих мастер-классов.")
        return
    # Сортируем даты и формируем кнопки для выбора дня с указанием дня недели
    sorted_dates = sorted(workshops_by_date.keys())
    buttons = []
    for date_obj in sorted_dates:
        day_name = DAYS_RU.get(date_obj.strftime("%A"), "")
        # Форматируем текст кнопки: (день недели)DD.MM.YYYY
        date_display = f"{day_name} - {date_obj.day} {months[date_obj.month]}"
        buttons.append([InlineKeyboardButton(text=date_display, callback_data=f"workshop_{date_obj.isoformat()}")])
    # Добавляем кнопку "Назад" для возврата в главное меню
    buttons.append([InlineKeyboardButton(text=back, callback_data="workshop_main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    # Сохраняем сгруппированные данные в состоянии
    await state.update_data(workshops_by_date={d.isoformat(): workshops_by_date[d] for d in workshops_by_date})
    await message.answer("Выбери день:", reply_markup=kb)

@router.callback_query(F.data == "workshop_main_menu")
async def workshop_main_menu(callback: CallbackQuery, state: FSMContext):
    """Возвращает пользователя в главное меню, используя сохранённую роль из состояния."""
    await callback.answer()
    data = await state.get_data()
    
    role = data.get("authorized_role")
    
    if role == "companion":
        from handlers.chaperone import show_chaperone_menu
        await show_chaperone_menu(callback.message, state)
    elif role == "speaker":
        from handlers.speaker import conference_back
        await callback.answer()
        await callback.message.delete()
        # await conference_back(callback.message, state)
    else:
        # Если переменная не установлена, пытаемся определить по наличию данных
        if data.get("teacher") and data.get("projects"):
            from handlers.chaperone import show_chaperone_menu
            await show_chaperone_menu(callback.message, state)
        elif data.get("speaker"):
            from handlers.speaker import conference_back
            await callback.answer()
            await callback.message.delete()
            # await conference_back(callback.message, state)
        else:
            # Базовый вариант
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Моя конференция 📅", callback_data="show_conference")],
                [InlineKeyboardButton(text="Мастер-классы 📐", callback_data="show_workshops")]
            ])
            try:
                await callback.message.edit_text("Главное меню:", reply_markup=main_menu_kb)
            except Exception:
                await callback.message.answer("Главное меню:", reply_markup=main_menu_kb)



@router.callback_query(F.data == "show_workshops")
async def callback_show_workshops(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие кнопки "Мастер-классы 📐" из главного меню спикера,
    вызывая функцию list_workshop_days.
    """
    await callback.answer()
    await list_workshop_days(callback.message, state)


@router.callback_query(F.data.startswith("workshop_") & ~F.data.in_(["workshop_back"]))
async def list_workshops_on_day(callback: CallbackQuery, state: FSMContext):
    """Показывает мастер-классы на выбранный день с кнопками-ссылками и кнопкой 'Назад'."""
    await callback.answer()
    # Извлекаем дату из callback_data, например, "workshop_2025-03-25"
    iso_date = callback.data.split("_", 1)[1]
    data = await state.get_data()
    workshops_by_date = data.get("workshops_by_date", {})
    events = workshops_by_date.get(iso_date)
    if not events:
        await callback.message.answer("Мероприятия не найдены или уже недоступны.")
        return
    date_obj = datetime.fromisoformat(iso_date).date()
    day_name = DAYS_RU.get(date_obj.strftime("%A"), "")
    # Форматируем дату с днем недели для сообщения
    date_str = f"{day_name} - {date_obj.day} {months[date_obj.month]}"
    # Формируем inline клавиатуру: каждая кнопка – мастер-класс с URL-ссылкой
    buttons = []
    for ev in events:
        time = ev.get('time', '')
        title = ev.get('title', 'Без названия')
        link = ev.get('link')
        button_text = f"{time} — {title}" if time else title
        if link:
            buttons.append([InlineKeyboardButton(text=button_text, url=link)])
        else:
            buttons.append([InlineKeyboardButton(text=button_text, callback_data="no_link")])
    # Добавляем кнопку "Назад" для возврата к выбору дня
    buttons.append([InlineKeyboardButton(text=back, callback_data="workshop_back")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer(f"*Мастер-классы на {date_str}:*", reply_markup=kb, parse_mode="Markdown", disable_web_page_preview=True)

@router.callback_query(F.data == "workshop_back")
async def workshop_back(callback: CallbackQuery, state: FSMContext):
    """Возвращает пользователя к выбору дня мастер-классов с указанием дня недели в кнопках."""
    await callback.message.delete()
    from datetime import date  # убедимся, что импортирован
    await callback.answer()
    data = await state.get_data()
    workshops_by_date = data.get("workshops_by_date")
    if not workshops_by_date:
        await callback.message.answer("Нет предстоящих мастер-классов.")
        return
    sorted_dates = sorted([date.fromisoformat(d) for d in workshops_by_date.keys()])
    # Словарь для перевода английских названий дней недели в русские сокращения
    DAYS_RU = {
        "Monday": "Пн",
        "Tuesday": "Вт",
        "Wednesday": "Ср",
        "Thursday": "Чт",
        "Friday": "Пт",
        "Saturday": "Сб",
        "Sunday": "Вс"
    }
    buttons = []
    for date_obj in sorted_dates:
        day_name = DAYS_RU.get(date_obj.strftime("%A"), "")
        date_display = f"({day_name}){format_datetime(date_obj.isoformat())}"
        buttons.append([InlineKeyboardButton(text=date_display, callback_data=f"workshop_{date_obj.isoformat()}")])
    # Добавляем кнопку "Назад" для возврата в главное меню выбора конференции/мастер-классов
    buttons.append([InlineKeyboardButton(text=back, callback_data="workshop_main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    # await callback.message.answer("Выбери день:", reply_markup=kb)
