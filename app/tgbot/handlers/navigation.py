from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from app.tgbot.states.booking import BookingStates
from app.tgbot.keyboards.booking import get_admin_menu_inline_keyboard, get_main_menu_inline_keyboard

async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingStates.waiting_for_action)
    # Получаем данные о статусе админа
    user_data = await state.get_data()
    is_admin = user_data.get('is_admin', False)
    
    await callback.message.edit_text(
        "Расскажи, как и что ты хочешь?",
        reply_markup=get_admin_menu_inline_keyboard() if is_admin else get_main_menu_inline_keyboard()
    ) 