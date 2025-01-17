from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from datetime import datetime, timedelta

from app.tgbot.handlers.navigation import back_to_main
from app.tgbot.utils.booking import get_available_dates
from config.config import settings
from logging import getLogger

from app.tgbot.filters.admin import IsAdmin
from app.tgbot.states.booking import BookingStates
from app.tgbot.keyboards.booking import (
    get_admin_menu_inline_keyboard, 
    get_all_bookings_keyboard, 
    get_dates_keyboard,
    get_back_to_admin_menu_keyboard
)
from app.infrastructure.database.repositories.booking_repository import BookingRepository
from app.infrastructure.google.sheets_service import GoogleSheetsService
from app.schemas.booking import BookingFilter, BookingStatus

admin_router = Router()
logger = getLogger(__name__)
admin_router.callback_query.filter(IsAdmin())
admin_router.message.filter(IsAdmin())

@admin_router.callback_query(lambda c: c.data == "block_day")
async def handle_block_day(
    callback: CallbackQuery,
    state: FSMContext,
    sheets_service: GoogleSheetsService
):
    available_dates = await get_available_dates(sheets_service)
    await state.set_state(BookingStates.waiting_for_block_day)
    await callback.message.edit_text(
        "Выберите день для блокировки:",
        reply_markup=get_dates_keyboard(available_dates)
    )

@admin_router.callback_query(BookingStates.waiting_for_block_day)
async def process_block_day(
    callback: CallbackQuery,
    state: FSMContext,
    sheets_service: GoogleSheetsService
):
    if callback.data == "back_to_main":
        await back_to_main(callback, state)
        return

    selected_date = callback.data.replace('date_', '')
    
    # Блокируем все слоты на выбранный день
    success = await sheets_service.block_day_in_sheets(selected_date)
    
    if success:
        await callback.message.edit_text(
            f"День {selected_date} успешно заблокирован! ✅",
            reply_markup=get_admin_menu_inline_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Произошла ошибка при блокировке дня. Попробуйте позже.",
            reply_markup=get_admin_menu_inline_keyboard()
        )

@admin_router.callback_query(lambda c: c.data == "manage_bookings")
async def handle_manage_bookings(
    callback: CallbackQuery,
    state: FSMContext,
    booking_repository: BookingRepository
):
    # Получаем все активные брони
    filters = BookingFilter(
        date_from=datetime.now().date(),
        status=BookingStatus.ACTIVE
    )
    
    bookings = await booking_repository.get_bookings(filters)
    
    if not bookings:
        await callback.message.edit_text(
            "Нет активных броней.",
            reply_markup=get_admin_menu_inline_keyboard()
        )
        return
    
    await state.set_state(BookingStates.admin_manage_bookings)
    await callback.message.edit_text(
        "Все активные брони:\nВыберите бронь для отмены:",
        reply_markup=get_all_bookings_keyboard(bookings)
    )

@admin_router.callback_query(
    BookingStates.admin_manage_bookings,
    lambda c: c.data.startswith("admin_cancel:")
)
async def handle_admin_cancel_booking(
    callback: CallbackQuery,
    state: FSMContext,
    booking_repository: BookingRepository,
    sheets_service: GoogleSheetsService
):
    booking_id = int(callback.data.replace('admin_cancel:', ''))
    booking = await booking_repository.get_booking(booking_id)
    
    if not booking:
        await callback.message.edit_text(
            "Бронь не найдена.",
            reply_markup=get_admin_menu_inline_keyboard()
        )
        return
    
    # Отменяем бронь
    await booking_repository.update_booking_status(booking_id, BookingStatus.CANCELLED)
    
    # Очищаем ячейки в Google Sheets
    await sheets_service.clear_booking_in_sheets(
        date_str=booking.booking_date.strftime('%d.%m.%y'),
        start_time=booking.start_time.strftime('%H:%M'),
        end_time=booking.end_time.strftime('%H:%M'),
        table_id=booking.table_id
    )
    
    await callback.message.edit_text(
        f"Бронь пользователя {booking.client_name} ({booking.client_phone}) успешно отменена!",
        reply_markup=get_admin_menu_inline_keyboard()
    )

@admin_router.callback_query(lambda c: c.data == "start_booking")
async def handle_admin_booking(
    callback: CallbackQuery, 
    state: FSMContext,
):
    await state.set_state(BookingStates.admin_waiting_for_client_name)
    await callback.message.edit_text(
        "Введите имя клиента:",
        reply_markup=get_back_to_admin_menu_keyboard()
    )

@admin_router.message(BookingStates.admin_waiting_for_client_name)
async def process_admin_client_name(
    message: Message,
    state: FSMContext,
):
    await state.update_data(client_name=message.text.strip())
    await state.set_state(BookingStates.admin_waiting_for_client_phone)
    await message.answer(
        "Введите номер телефона клиента:",
        reply_markup=get_back_to_admin_menu_keyboard()
    )

@admin_router.message(BookingStates.admin_waiting_for_client_phone)
async def process_admin_client_phone(
    message: Message,
    state: FSMContext,
    sheets_service: GoogleSheetsService
):
    phone = message.text.strip()
    await state.update_data(client_phone=phone)
    
    available_dates = await get_available_dates(sheets_service)
    if not available_dates:
        await message.answer(
            "На ближайшие дни все занято!",
            reply_markup=get_admin_menu_inline_keyboard()
        )
        return

    await state.set_state(BookingStates.waiting_for_date)
    await message.answer(
        "Выберите день:",
        reply_markup=get_dates_keyboard(available_dates, is_admin=True)
    ) 