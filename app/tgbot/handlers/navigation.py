from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from app.tgbot.states.booking import BookingStates
from app.tgbot.keyboards.booking import (
    get_admin_menu_inline_keyboard, 
    get_main_menu_inline_keyboard,
    get_dates_keyboard,
    get_time_keyboard
)
from app.tgbot.utils.booking import get_available_dates, get_available_times

async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingStates.waiting_for_action)
    # Получаем данные о статусе админа
    user_data = await state.get_data()
    is_admin = user_data.get('is_admin', False)
    
    await callback.message.edit_text(
        "Расскажи, как и что ты хочешь?",
        reply_markup=get_admin_menu_inline_keyboard() if is_admin else get_main_menu_inline_keyboard()
    )

async def back_to_dates(
    callback: CallbackQuery, 
    state: FSMContext,
    sheets_service
):
    available_dates = await get_available_dates(sheets_service)
    await state.set_state(BookingStates.waiting_for_date)
    user_data = await state.get_data()
    keyboard = get_dates_keyboard(available_dates, is_admin=user_data.get('is_admin', False))
    
    await callback.message.edit_text(
        "Выбери день:",
        reply_markup=keyboard
    )

async def back_to_start_time(
    callback: CallbackQuery, 
    state: FSMContext,
    sheets_service
):
    state_data = await state.get_data()
    table_pref = state_data.get('table_preference', 'random')
    available_times = await get_available_times(sheets_service, state_data['selected_date'], table_pref)
    
    await state.set_state(BookingStates.waiting_for_start_time)
    keyboard = get_time_keyboard(available_times, is_admin=state_data.get('is_admin', False))
    
    await callback.message.edit_text(
        "Выбери, с которого часа начнём:",
        reply_markup=keyboard
    ) 