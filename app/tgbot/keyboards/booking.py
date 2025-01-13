from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="Посмотреть свободное местечко")],
        [KeyboardButton(text="Забронировать бильярдный столик в The Feel's")],
        [KeyboardButton(text="Отменить существующую бронь")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_dates_keyboard(available_dates: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for date in available_dates:
        builder.button(
            text=f"{date['date']} ({date['weekday']})", 
            callback_data=f"date_{date['date']}"
        )
    builder.adjust(2)
    return builder.as_markup()

def get_time_keyboard(available_times: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for time in available_times:
        builder.button(
            text=time,
            callback_data=f"time_{time}"
        )
    builder.adjust(3)
    return builder.as_markup() 