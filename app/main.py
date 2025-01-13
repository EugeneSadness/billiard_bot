import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Токен вашего бота
bot = Bot(token='8027406175:AAGwjmpoxSvok-BGqmoQkNll-mhF3jiQYLk')

# Диспетчер и хранилище состояний в памяти
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния FSM
class BookingStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_phone = State()

# Создаём основную клавиатуру
def get_main_keyboard():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Посмотреть свободное местечко")],
            [KeyboardButton(text="Забронировать бильярдный столик")],
            [KeyboardButton(text="Отменить бронь")]
        ],
        resize_keyboard=True
    )
    return kb

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет, дорогуша!\n"
        "Я вирт. помощник Анжелла\n"
        "Расскажи, как и что ты хочешь?",
        reply_markup=get_main_keyboard()
    )

# Обработчик кнопки бронирования
@dp.message(lambda message: message.text == "Забронировать бильярдный столик")
async def process_booking_start(message: types.Message, state: FSMContext):
    await state.set_state(BookingStates.waiting_for_name)
    await message.answer("Как твоё имя, дорогуша?")

# Обработчик ввода имени
@dp.message(BookingStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(user_name=message.text)
    await state.set_state(BookingStates.waiting_for_date)
    # Здесь можно добавить клавиатуру с датами
    await message.answer(f"Приятно познакомиться, {message.text}!\nВыбери день:")

# Обработчик просмотра свободного времени
@dp.message(lambda message: message.text == "Посмотреть свободное местечко")
async def process_view_schedule(message: types.Message):
    await message.answer("Дорогуша, пока что функционал в разработке!")

# Обработчик отмены брони
@dp.message(lambda message: message.text == "Отменить бронь")
async def process_cancel_booking(message: types.Message):
    await message.answer("Дорогуша, пока что функционал в разработке!")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
