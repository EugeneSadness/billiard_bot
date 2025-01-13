from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Посмотреть свободное местечко")],
            [KeyboardButton(text="Забронировать бильярдный столик")],
            [KeyboardButton(text="Отменить бронь")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_date_keyboard(available_dates):
    buttons = []
    for date in available_dates:
        buttons.append([InlineKeyboardButton(
            text=f"{date['date']} ({date['weekday']})",
            callback_data=f"date_{date['date']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_time_keyboard(available_times):
    buttons = []
    for time in available_times:
        buttons.append([InlineKeyboardButton(
            text=time,
            callback_data=f"time_{time}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
