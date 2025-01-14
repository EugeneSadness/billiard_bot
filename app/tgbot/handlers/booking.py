from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from app.tgbot.states.booking import BookingStates
from app.tgbot.keyboards.booking import get_main_menu_keyboard, get_dates_keyboard, get_time_keyboard
from app.tgbot.utils.booking import get_available_dates, get_available_times
from app.infrastructure.google.sheets_service import GoogleSheetsService
from app.infrastructure.database.repositories.booking_repository import BookingRepository
from app.schemas.booking import BookingCreate

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
async def process_name(message: Message, state: FSMContext):
    await state.update_data(client_name=message.text)
    available_dates = get_available_dates()
    await state.set_state(BookingStates.waiting_for_date)
    await message.answer(
        f"Приятно познакомиться, {message.text}!\n\nВыбери день:",
        reply_markup=get_dates_keyboard(available_dates)
    ) 

@booking_router.callback_query(BookingStates.waiting_for_date)
async def process_date(callback: CallbackQuery, state: FSMContext):
    selected_date = callback.data.replace('date_', '')
    await state.update_data(selected_date=selected_date)
    
    available_times = get_available_times(selected_date)
    await state.set_state(BookingStates.waiting_for_start_time)
    await callback.message.edit_text(
        "Выбери, с которого часа",
        reply_markup=get_time_keyboard(available_times)
    )

@booking_router.message(BookingStates.confirm_booking)
async def confirm_booking(
    message: Message,
    state: FSMContext,
    booking_repository: BookingRepository,
    sheets_service: GoogleSheetsService
):
    if message.text.lower() == "да":
        # Получаем данные из состояния
        booking_data = await state.get_data()
        
        # Создаем бронь в БД
        booking = await booking_repository.create_booking(
            BookingCreate(**booking_data)
        )
        
        # Записываем в Google Sheets
        await sheets_service.add_booking({
            'date': booking_data['booking_date'],
            'start_time': booking_data['start_time'],
            'client_name': booking_data['client_name'],
            'phone': booking_data['client_phone'],
            'table_id': booking_data['table_id']
        })
        
        await message.answer("Отлично! Я записала тебя, дорогуша!")
        await state.clear()
    else:
        await message.answer("Бронирование отменено")
        await state.clear()