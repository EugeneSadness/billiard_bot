from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.tgbot.keyboards.menu import get_main_menu, get_date_keyboard
from app.tgbot.states.booking import BookingStates
from app.tgbot.utils.booking import get_available_dates

router = Router()

@router.message(commands=["start"])
async def cmd_start(message: Message):
    await message.answer(
        "Привет, дорогуша!\n"
        "Я вирт. помощник Анжелла\n"
        "Расскажи, как и что ты хочешь?",
        reply_markup=get_main_menu()
    )

@router.message(F.text == "Забронировать бильярдный столик")
async def start_booking(message: Message, state: FSMContext):
    await state.set_state(BookingStates.ENTER_NAME)
    await message.answer("Отлично! Давай я помогу тебе, и мы вместе сделаем это\nКак твоё имя, дорогуша?")

@router.message(BookingStates.ENTER_NAME)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(BookingStates.SELECT_DATE)
    available_dates = get_available_dates()  # Функция получения доступных дат
    await message.answer(
        f"Приятно познакомиться, {message.text}!\nВыбери день:",
        reply_markup=get_date_keyboard(available_dates)
    )

# Дополнительные обработчики для остальных состояний
