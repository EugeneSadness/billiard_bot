from datetime import datetime
from logging import getLogger

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from app.tgbot.handlers.admin import handle_admin_booking
from app.tgbot.handlers.navigation import back_to_main
from app.infrastructure.database.repositories.booking_repository import BookingRepository
from app.infrastructure.database.repositories.client_repository import ClientRepository
from app.infrastructure.google.sheets_service import GoogleSheetsService
from app.schemas.booking import BookingCreate, BookingFilter, BookingStatus
from app.tgbot.keyboards.booking import (
    get_dates_keyboard, 
    get_time_keyboard, 
    get_end_time_keyboard,
    get_main_menu_inline_keyboard, 
    get_cancel_booking_keyboard, 
    get_admin_menu_inline_keyboard,
    get_table_preference_keyboard
)
from app.tgbot.states.booking import BookingStates
from app.tgbot.utils.booking import get_available_dates, get_available_times
from app.tgbot.utils.date_helpers import format_date_with_weekday
from config.config import settings
booking_router = Router()
logger = getLogger(__name__)

@booking_router.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    await state.set_state(BookingStates.waiting_for_action)
    
    # Проверяем, является ли пользователь администратором
    is_admin = message.from_user.username == settings.ADMIN_NAME
    
    await message.answer(
        "Привет, дорогуша 🩷\n\n"
        "Я вирт. помощник Анжелла🍓\n\n"
        "Расскажи, как и что ты хочешь?",
        reply_markup=get_admin_menu_inline_keyboard() if is_admin else get_main_menu_inline_keyboard(),
    )

@booking_router.callback_query(lambda c: c.data == "start_booking")
async def handle_booking_callback(
    callback: CallbackQuery, 
    state: FSMContext,
    sheets_service: GoogleSheetsService
):
    user_data = await state.get_data()
    
    # Если это админ, перенаправляем на админский обработчик
    if user_data.get('is_admin'):
        await handle_admin_booking(callback, state)
        return

    if user_data.get('client_name'):
        await state.set_state(BookingStates.waiting_for_date)
        available_dates = await get_available_dates(sheets_service)
        await callback.message.edit_text(
            f"С возвращением, {user_data['client_name']}!\n\nВыбери день:",
            reply_markup=get_dates_keyboard(available_dates)
        )
    else:
        await state.set_state(BookingStates.waiting_for_name)
        await callback.message.edit_text(
            "Отлично! \n\n"
            "Давай я помогу тебе, и мы вместе сделаем это 💋\n\n"
            "Как твоё имя, дорогуша?"
        )

@booking_router.message(BookingStates.waiting_for_name)
async def process_name(
    message: Message, 
    state: FSMContext,
    sheets_service: GoogleSheetsService
):
    name = message.text.strip()
    is_admin = name == settings.ADMIN_NAME
    
    await state.update_data(
        client_name=name,
        is_admin=is_admin
    )
    
    if is_admin:
        await message.answer(
            f"Добро пожаловать, администратор! 👑\n\n"
            "Вам доступны расширенные функции управления.",
            reply_markup=get_admin_menu_inline_keyboard()
        )
        await state.set_state(BookingStates.waiting_for_action)
        return

    # Обычный процесс для не-админа
    available_dates = await get_available_dates(sheets_service)
    
    if not available_dates:
        await message.answer("Извини, дорогуша, но на ближайшие дни все занято!")
        await state.clear()
        return
        
    await state.set_state(BookingStates.waiting_for_date)
    await message.answer(
        f"Приятно познакомиться, {name}!🫶\n\nВыбери день:",
        reply_markup=get_dates_keyboard(available_dates)
    )

@booking_router.callback_query(BookingStates.waiting_for_date)
async def process_date(
    callback: CallbackQuery, 
    state: FSMContext,
    sheets_service: GoogleSheetsService
):
    if callback.data == "back_to_main":
        await back_to_main(callback, state)
        return
        
    selected_date = callback.data.replace('date_', '')
    await state.update_data(selected_date=selected_date)

    state_data = await state.get_data()
    is_admin = state_data.get('is_admin', False)
    if is_admin:
        await state.set_state(BookingStates.waiting_for_table_preference)
        await callback.message.edit_text(
            "За каким столом будет клиент?",
            reply_markup=get_table_preference_keyboard()
        )
    else:
        # Вместо перехода к выбору времени, спрашиваем о предпочтительном столе
        await state.set_state(BookingStates.waiting_for_table_preference)
        await callback.message.edit_text(
            f"За каким столом предпочитаешь сделать это, {state_data['client_name']}? 😼\n\n"
            f"(Цена удовольствия составляет всего 1200 руб./час)",
            reply_markup=get_table_preference_keyboard()
        )

# Новый обработчик для выбора стола
@booking_router.callback_query(BookingStates.waiting_for_table_preference)
async def process_table_preference(
    callback: CallbackQuery,
    state: FSMContext,
    sheets_service: GoogleSheetsService
):
    if callback.data == "back_to_dates":
        await back_to_dates(callback, state, sheets_service)
        return

    table_pref = callback.data.replace('table_pref:', '')
    await state.update_data(table_preference=table_pref)
    
    # Получаем данные о дате из состояния
    state_data = await state.get_data()
    selected_date = state_data['selected_date']
    
    # Получаем доступное время с учетом предпочтительного стола
    available_times = await get_available_times(sheets_service, selected_date, table_pref)
    
    if not available_times:
        await callback.message.edit_text(
            "Извини, но на этот день все часы для выбранного стола заняты! "
            "Попробуй выбрать другой стол или день:",
            reply_markup=get_table_preference_keyboard()
        )
        return
        
    await state.set_state(BookingStates.waiting_for_start_time)
    await callback.message.edit_text(
        "Выбери, с которого часа начнём удовольствия:",
        reply_markup=get_time_keyboard(available_times)
    )

@booking_router.callback_query(BookingStates.waiting_for_start_time)
async def process_start_time(
    callback: CallbackQuery,
    state: FSMContext,
    sheets_service: GoogleSheetsService
):
    if callback.data == "back_to_dates":
        await back_to_dates(callback, state, sheets_service)
        return
        
    start_time = callback.data.replace('time:', '')
    state_data = await state.get_data()
    is_admin = state_data.get('is_admin', False)
    table_preference = state_data.get('table_preference')
    
    
    if table_preference == 'random':
        best_table, available_end_times = await sheets_service.get_best_table_and_end_times(
            state_data['selected_date'],
            start_time
        )
    else:
        # Преобразуем строку с номером стола в число
        requested_table = int(table_preference)
        # Проверяем доступность конкретного стола
        available_end_times = await sheets_service.get_available_end_times_for_table(
            state_data['selected_date'],
            start_time,
            requested_table
        )
        best_table = requested_table if available_end_times else None
    
    if not best_table or not available_end_times:
        await callback.message.edit_text(
            "Извини, но на это время нет свободных столов! Выбери другое время:",
            reply_markup=get_admin_menu_inline_keyboard() if is_admin else get_main_menu_inline_keyboard()
        )
        return
    
    await state.update_data(
        start_time=start_time,
        table_id=best_table
    )
    
    await state.set_state(BookingStates.waiting_for_end_time)
    await callback.message.edit_text(
        "Выбери, когда заканчиваем наши игры:",
        reply_markup=get_end_time_keyboard(available_end_times)
    )

@booking_router.callback_query(BookingStates.waiting_for_end_time)
async def process_end_time(
    callback: CallbackQuery,
    state: FSMContext,
    sheets_service: GoogleSheetsService,
    booking_repository: BookingRepository,
    client_repository: ClientRepository
):
    # Проверяем навигационные команды
    if callback.data == "back_to_start_time":
        await back_to_start_time(callback, state, sheets_service)
        return
        
    end_time = callback.data.replace('end_time:', '')
    await state.update_data(end_time=end_time)
    
    user_data = await state.get_data()
    
    # Проверяем, есть ли уже сохраненный телефон
    if user_data.get('client_phone'):
        await process_booking(callback.message, state, sheets_service, booking_repository, client_repository)
    else:
        # Если телефона нет, запрашиваем его
        await state.set_state(BookingStates.waiting_for_phone)
        await callback.message.edit_text(
            "Напиши мне свой номерок 😉"
        )

@booking_router.message(BookingStates.waiting_for_phone)
async def process_phone(
    message: Message,
    state: FSMContext,
    sheets_service: GoogleSheetsService,
    booking_repository: BookingRepository,
    client_repository: ClientRepository
):
    await state.update_data(client_phone=message.text)
    await process_booking(message, state, sheets_service, booking_repository, client_repository)

# Выносим логику создания бронирования в отдельную функцию
async def process_booking(
    message: Message,
    state: FSMContext,
    sheets_service: GoogleSheetsService,
    booking_repository: BookingRepository,
    client_repository: ClientRepository
):
    try:
        booking_data = await state.get_data()
        
        # Сначала проверяем, существует ли клиент
        existing_client = await client_repository.get_client_by_phone(phone=booking_data.get('client_phone'))
        # Преобразуем строку даты в объект datetime
        visit_date = datetime.strptime(booking_data['selected_date'], '%d.%m.%y')
        is_admin = booking_data.get('is_admin', False)

        if not existing_client:
            

            # Если клиент новый - создаем запись
            client = await client_repository.create_client(
                name=booking_data['client_name'],
                phone=booking_data['client_phone'],
                visit_date=visit_date
            )
            client_id = client.id
        else:
            # Обновляем дату последнего посещения
            await client_repository.update_visit_date(
                client_id=existing_client.id,
                visit_date=visit_date
            )
            client_id = existing_client.id
        
        # Преобразуем строки в объекты date и time
        booking_date = datetime.strptime(booking_data['selected_date'], '%d.%m.%y').date()
        start_time = datetime.strptime(booking_data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(booking_data['end_time'], '%H:%M').time()
        
        # Создаем объект бронирования
        booking = BookingCreate(
            table_id=booking_data['table_id'],
            client_name=booking_data['client_name'],
            client_id=client_id,
            client_phone=booking_data['client_phone'],
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time
        )

        # Сохраняем бронирование
        await booking_repository.create_booking(booking)

        # Обновляем Google Sheets
        sheets_updated = await sheets_service.update_booking_in_sheets(
            date_str=booking_data['selected_date'],
            start_time=booking_data['start_time'],
            end_time=booking_data['end_time'],
            table_id=booking_data['table_id'],
            client_name=booking_data['client_name'],
            client_phone=booking_data['client_phone']
        )

        if not sheets_updated:
            logger.warning("Failed to update Google Sheets")

        
        
        date_str, weekday_ru = format_date_with_weekday(booking_data['selected_date'])
        await message.answer(
            f"Отлично, дорогуша!\n"
            f"Время наслаждений забронировано с {booking_data['start_time']} "
            f"до {booking_data['end_time']}, "
            f"{date_str} ({weekday_ru}), "
            f"жду тебя в The Feel's 🩷\n\n"
            "Пожалуйста, ознакомься с правилами нашей игры 🙌"
        )
        
        await message.answer(
            "Правила нашего бильярдного клуба 🩷\n\n"
            "+ пожалуйста, бери кии только рядом со своим столом, и три их мелком цвета, "
            "соответствующего цвету сукна. Другой цвет мела оставляет следы 💦\n\n"
            "+ пожалуйста, не ставь напитки на сукно и борты стола, чтобы случайно не пролить. "
            "За пролитие напитков на стол придётся внести 3000 руб. взноса за хим. чистку.\n"
            "(Если интересно, то перетянуть новое сукно стоит 25 000 руб.) 💵\n\n"
            "+ пожалуйста, приходи во время, столик принадлежит тебе на всё время брони, "
            "а другим мы отказываем. Поэтому, если вы пришли позже, стоить он будет "
            "соответственно забронированному времени ⏰"
        )
        
        await message.answer(
            "Хэй, дорогуша, и обязательно подпишись на наш телеграм-канал! 🩷\n\n"
            "@thefeels_billiard\n\n"
            "Жду 🫦"
        )

        await message.answer(
            "Посмотреть, как пройти к нам:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        text="Показать маршрут 🗺️",
                        callback_data="how_to_find_us"
                    )
                ]]
            )
        )

        await state.set_state(BookingStates.waiting_for_action)
        await message.answer(
            "Расскажи, как и что ты хочешь?",
            reply_markup=get_admin_menu_inline_keyboard() if is_admin else get_main_menu_inline_keyboard()
        )
        
    except Exception as e:
        user_data = await state.get_data()
        is_admin = user_data.get('is_admin', False)
        
        await message.answer(
            "Извини, произошла ошибка при сохранении бронирования. "
            "Попробуй, пожалуйста, позже или свяжись с администратором.",
            reply_markup=get_admin_menu_inline_keyboard() if is_admin else get_main_menu_inline_keyboard()
        )
        logger.error(f"Error creating booking: {e}")
    
    # Не очищаем состояние полностью, а только убираем данные бронирования
    await state.update_data(
        selected_date=None,
        start_time=None,
        end_time=None,
        table_id=None
    )

@booking_router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingStates.waiting_for_action)
    # Получаем данные о статусе админа
    user_data = await state.get_data()
    is_admin = user_data.get('is_admin', False)
    
    await callback.message.edit_text(
        "Расскажи, как и что ты хочешь?",
        reply_markup=get_admin_menu_inline_keyboard() if is_admin else get_main_menu_inline_keyboard()
    )

@booking_router.callback_query(lambda c: c.data == "back_to_dates")
async def back_to_dates(
    callback: CallbackQuery, 
    state: FSMContext,
    sheets_service: GoogleSheetsService
):
    available_dates = await get_available_dates(sheets_service)
    await state.set_state(BookingStates.waiting_for_date)
    # Получаем данные о статусе админа для кнопки "назад"
    user_data = await state.get_data()
    keyboard = get_dates_keyboard(available_dates, is_admin=user_data.get('is_admin', False))
    
    await callback.message.edit_text(
        "Выбери день:",
        reply_markup=keyboard
    )

@booking_router.callback_query(lambda c: c.data == "back_to_start_time")
async def back_to_start_time(
    callback: CallbackQuery, 
    state: FSMContext,
    sheets_service: GoogleSheetsService
):
    state_data = await state.get_data()
    table_pref = state_data.get('table_preference', 'random')  # Get the stored table preference
    available_times = await get_available_times(sheets_service, state_data['selected_date'], table_pref)
    
    await state.set_state(BookingStates.waiting_for_start_time)
    # Получаем данные о статусе админа для кнопки "назад"
    keyboard = get_time_keyboard(available_times, is_admin=state_data.get('is_admin', False))
    
    await callback.message.edit_text(
        "Выбери, с которого часа начнём:",
        reply_markup=keyboard
    )

@booking_router.callback_query(lambda c: c.data == "my_bookings")
async def handle_my_bookings(
    callback: CallbackQuery,
    state: FSMContext,
    booking_repository: BookingRepository
):
    user_data = await state.get_data()
    if not user_data.get('client_phone'):
        await callback.message.edit_text(
            "Чтобы посмотреть свои брони, сначала сделай хотя бы одно бронирование 😉",
            reply_markup=get_main_menu_inline_keyboard()
        )
        return

    # Получаем текущую дату и время
    now = datetime.now()
    
    # Создаем фильтр для поиска броней
    filters = BookingFilter(
        client_phone=user_data['client_phone'],
        date_from=now.date(),
        status=BookingStatus.ACTIVE
    )
    
    # Получаем брони пользователя
    bookings = await booking_repository.get_bookings(filters)
    
    if not bookings:
        await callback.message.edit_text(
            "У тебя пока нет активных броней, дорогуша! 😊\n"
            "Хочешь забронировать столик?",
            reply_markup=get_main_menu_inline_keyboard()
        )
        return

    # Формируем сообщение со списком броней
    message_text = "Твои брони, дорогуша:\n\n"
    for booking in bookings:
        date_str, weekday_ru = format_date_with_weekday(booking.booking_date.strftime('%d.%m.%y'))
        message_text += (
            f"📅 {date_str} ({weekday_ru})\n"
            f"🕒 {booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}\n"
            f"🎱 Стол: {booking.table.name}\n\n"
        )
    
    message_text += "Хочешь забронировать ещё?"
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_main_menu_inline_keyboard()
    )

@booking_router.callback_query(lambda c: c.data == "cancel_booking")
async def handle_cancel_booking(
    callback: CallbackQuery,
    state: FSMContext,
    booking_repository: BookingRepository
):
    user_data = await state.get_data()
    if not user_data.get('client_phone'):
        await callback.message.edit_text(
            "Чтобы отменить бронь, сначала нужно сделать хотя бы одно бронирование 😉",
            reply_markup=get_main_menu_inline_keyboard()
        )
        return

    # Получаем активные брони пользователя
    filters = BookingFilter(
        client_phone=user_data['client_phone'],
        date_from=datetime.now().date(),
        status=BookingStatus.ACTIVE
    )
    
    bookings = await booking_repository.get_bookings(filters)
    
    if not bookings:
        await callback.message.edit_text(
            "У тебя нет активных броней для отмены, дорогуша! 😊",
            reply_markup=get_main_menu_inline_keyboard()
        )
        return
    
    await state.set_state(BookingStates.select_booking_to_cancel)
    await callback.message.edit_text(
        "Выбери бронь, которую хочешь отменить:",
        reply_markup=get_cancel_booking_keyboard(bookings)
    )

@booking_router.callback_query(BookingStates.select_booking_to_cancel)
async def handle_booking_cancellation(
    callback: CallbackQuery,
    state: FSMContext,
    booking_repository: BookingRepository,
    sheets_service: GoogleSheetsService
):
    if callback.data == "back_to_main":
        await back_to_main(callback, state)
        return
        
    booking_id = int(callback.data.replace('cancel_booking:', ''))
    booking = await booking_repository.get_booking(booking_id)
    
    
    if not booking:
        await callback.message.edit_text(
            "Извини, но эта бронь уже недоступна.",
            reply_markup=get_main_menu_inline_keyboard()
        )
        return
    
    # Отменяем бронь
    await booking_repository.update_booking_status(booking_id, BookingStatus.CANCELLED)
    
    # Обновляем Google Sheets (очищаем ячейки)
    await sheets_service.clear_booking_in_sheets(
        date_str=booking.booking_date.strftime('%d.%m.%y'),
        start_time=booking.start_time.strftime('%H:%M'),
        end_time=booking.end_time.strftime('%H:%M'),
        table_id=booking.table_id
    )
    
    date_str, weekday_ru = format_date_with_weekday(booking.booking_date.strftime('%d.%m.%y'))
    await callback.message.edit_text(
        f"Бронь на {date_str} ({weekday_ru}) "
        f"с {booking.start_time.strftime('%H:%M')} до {booking.end_time.strftime('%H:%M')} "
        f"успешно отменена! 👌",
        reply_markup=get_main_menu_inline_keyboard()
    )
    
    await state.set_state(BookingStates.waiting_for_action)

@booking_router.callback_query(lambda c: c.data == "unblock_day")
async def handle_unblock_day(
    callback: CallbackQuery,
    state: FSMContext,
    sheets_service: GoogleSheetsService
):
    # Получаем доступные даты (все даты из таблицы)
    data = await sheets_service.get_sheet_data()
    available_dates = []
    
    if not data or len(data) < 3:
        await callback.message.edit_text(
            "Не удалось получить даты из таблицы.",
            reply_markup=get_admin_menu_inline_keyboard()
        )
        return
        
    # Получаем все даты из первого столбца
    for idx in range(3, len(data), 4):
        try:
            date_cell = data[idx][0]
            if date_cell and date_cell.strip():
                date = datetime.strptime(date_cell, '%d.%m')
                date = date.replace(year=datetime.now().year)
                available_dates.append({
                    'date': date.strftime('%d.%m.%y'),
                    'weekday': date.strftime('%A')
                })
        except (ValueError, AttributeError):
            continue
    
    if not available_dates:
        await callback.message.edit_text(
            "Нет доступных дат для разблокировки.",
            reply_markup=get_admin_menu_inline_keyboard()
        )
        return

    await state.set_state(BookingStates.waiting_for_block_day)
    await state.update_data(action='unblock')  # Сохраняем действие для различения блокировки/разблокировки
    await callback.message.edit_text(
        "Выберите день для разблокировки:",
        reply_markup=get_dates_keyboard(available_dates, is_admin=True)
    )

@booking_router.callback_query(BookingStates.waiting_for_block_day)
async def process_block_unblock_day(
    callback: CallbackQuery,
    state: FSMContext,
    sheets_service: GoogleSheetsService
):
    if callback.data == "back_to_main":
        await back_to_main(callback, state)
        return

    state_data = await state.get_data()
    action = state_data.get('action', 'block')  # По умолчанию блокировка
    selected_date = callback.data.replace('date_', '')
    
    success = False
    if action == 'block':
        success = await sheets_service.block_day_in_sheets(selected_date)
        message = "День успешно заблокирован!" if success else "Не удалось заблокировать день."
    else:  # unblock
        success = await sheets_service.unblock_day_in_sheets(selected_date)
        message = "День успешно разблокирован!" if success else "Не удалось разблокировать день."

    await state.set_state(BookingStates.waiting_for_action)
    await callback.message.edit_text(
        message,
        reply_markup=get_admin_menu_inline_keyboard()
    )

@booking_router.callback_query(lambda c: c.data == "how_to_find_us")
async def handle_how_to_find_us(callback: CallbackQuery, state: FSMContext):
    # First message with text
    await callback.message.answer(
        "The Feel's находится по адресу: ул. Пушкина, д. 7 🏠\n\n"
        "Вход со стороны улицы Пушкина, между магазином 'Красное и Белое' "
        "и кофейней 'Coffee Like' ☕️\n\n"
        "Спускайся по лестнице вниз, и ты попадёшь в наше уютное место 🩷"
    )
    
    # Send location photos (you'll need to prepare these media files)
    photo1 = FSInputFile("assets/the_feels.jpeg")
    photo2 = FSInputFile("assets/the_feels.jpeg")
    
    await callback.message.answer_photo(
        photo=photo1,
        caption="Вход в The Feel's 🚪"
    )
    
    await callback.message.answer_photo(
        photo=photo2,
        caption="Вид здания с улицы 🏢"
    )
    
    # Return to main menu
    user_data = await state.get_data()
    is_admin = user_data.get('is_admin', False)
    
    await callback.message.answer(
        "Расскажи, как и что ты хочешь?",
        reply_markup=get_admin_menu_inline_keyboard() if is_admin else get_main_menu_inline_keyboard()
    )

@booking_router.callback_query(lambda c: c.data == "contact_info")
async def handle_contact_info(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Контактная информация будет здесь...",
        reply_markup=get_main_menu_inline_keyboard()
    )

