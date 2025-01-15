from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from app.tgbot.states.booking import BookingStates
from app.tgbot.keyboards.booking import get_main_menu_keyboard, get_dates_keyboard, get_time_keyboard, get_end_time_keyboard
from app.tgbot.utils.booking import get_available_dates, get_available_times, get_available_end_times
from app.infrastructure.google.sheets_service import GoogleSheetsService
from app.infrastructure.database.repositories.booking_repository import BookingRepository
from app.schemas.booking import BookingCreate
from app.tgbot.utils.date_helpers import format_date_with_weekday

booking_router = Router()

@booking_router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет, дорогуша!\n\n"
        "Я вирт. помощник Анжелла\n\n"
        "Расскажи, как и что ты хочешь?",
        reply_markup=get_main_menu_keyboard()
    )

@booking_router.message(F.text == "Забронировать бильярдный столик в The Feel's")
async def start_booking(message: Message, state: FSMContext):
    await state.set_state(BookingStates.waiting_for_name)
    await message.answer("Отлично! Давай я помогу тебе, и мы вместе сделаем это\n\nКак твоё имя, дорогуша?")

@booking_router.message(BookingStates.waiting_for_name)
async def process_name(
    message: Message, 
    state: FSMContext,
    sheets_service: GoogleSheetsService
):
    await state.update_data(client_name=message.text)
    available_dates = await get_available_dates(sheets_service)
    
    if not available_dates:
        await message.answer("Извини, дорогуша, но на ближайшие дни все занято!")
        await state.clear()
        return
        
    await state.set_state(BookingStates.waiting_for_date)
    await message.answer(
        f"Приятно познакомиться, {message.text}!\n\nВыбери день:",
        reply_markup=get_dates_keyboard(available_dates)
    )

@booking_router.callback_query(BookingStates.waiting_for_date)
async def process_date(
    callback: CallbackQuery, 
    state: FSMContext,
    sheets_service: GoogleSheetsService
):
    selected_date = callback.data.replace('date_', '')
    await state.update_data(selected_date=selected_date)
    
    available_times = await get_available_times(sheets_service, selected_date)
    
    if not available_times:
        await callback.message.edit_text(
            "Извини, но на этот день все часы заняты! Выбери другой день:"
        )
        return
        
    await state.set_state(BookingStates.waiting_for_start_time)
    await callback.message.edit_text(
        "Выбери, с которого часа начнём:",
        reply_markup=get_time_keyboard(available_times)
    )

@booking_router.callback_query(BookingStates.waiting_for_start_time)
async def process_start_time(
    callback: CallbackQuery,
    state: FSMContext,
    sheets_service: GoogleSheetsService
):
    start_time = callback.data.replace('time:', '')
    state_data = await state.get_data()
    
    best_table, available_end_times = await sheets_service.get_best_table_and_end_times(
        state_data['selected_date'],
        start_time
    )
    
    if not best_table or not available_end_times:
        await callback.message.edit_text(
            "Извини, но на это время нет свободных столов! Выбери другое время:"
        )
        return
    
    await state.update_data(
        start_time=start_time,
        table_id=best_table
    )
    
    await state.set_state(BookingStates.waiting_for_end_time)
    await callback.message.edit_text(
        "Выбери, до которого часа играем:",
        reply_markup=get_end_time_keyboard(available_end_times)
    )

@booking_router.callback_query(BookingStates.waiting_for_end_time)
async def process_end_time(
    callback: CallbackQuery,
    state: FSMContext
):
    end_time = callback.data.replace('end_time:', '')
    await state.update_data(end_time=end_time)
    
    await state.set_state(BookingStates.waiting_for_phone)
    await callback.message.edit_text(
        "Напиши мне свой номерок 😉"
    )

@booking_router.message(BookingStates.waiting_for_phone)
async def process_phone(
    message: Message,
    state: FSMContext
):
    await state.update_data(client_phone=message.text)
    booking_data = await state.get_data()
    
    date_str, weekday_ru = format_date_with_weekday(booking_data['selected_date'])
    
    await message.answer(
        f"Отлично, дорогуша!\n"
        f"Время наслаждений забронировано с {booking_data['start_time']} "
        f"до {booking_data['end_time']}, "
        f"{date_str} ({weekday_ru}), "
        f"жду тебя в The Feel's 🩷"
    )
    
    # TODO: Сохранить бронирование в БД и Google Sheets
    await state.clear()