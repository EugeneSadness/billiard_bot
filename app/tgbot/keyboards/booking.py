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
    # Преобразуем времена в datetime для правильной сортировки
    def time_to_datetime(time_str):
        hour = int(time_str.split(':')[0])
        # Для времени после полуночи добавляем 24 часа для правильной сортировки
        if hour < 4:  # для времени 00:00 - 03:00
            hour += 24
        return hour

    # Сортируем времена
    sorted_times = sorted(available_times, key=time_to_datetime)
    
    keyboard = []
    current_row = []
    
    # Создаем кнопки
    for time in sorted_times:
        current_row.append(
            InlineKeyboardButton(
                text=time,
                callback_data=f"time:{time}"
            )
        )
        
        # Формируем ряды по 3 кнопки
        if len(current_row) == 3:
            keyboard.append(current_row)
            current_row = []
    
    # Добавляем оставшиеся кнопки
    if current_row:
        keyboard.append(current_row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 

def get_end_time_keyboard(available_end_times: list[str]) -> InlineKeyboardMarkup:
    # Преобразуем времена в datetime для правильной сортировки
    def time_to_datetime(time_str):
        hour = int(time_str.split(':')[0])
        # Для времени после полуночи добавляем 24 часа для правильной сортировки
        if hour < 4:  # для времени 00:00 - 03:00
            hour += 24
        return hour

    # Сортируем времена
    sorted_times = sorted(available_end_times, key=time_to_datetime)
    
    keyboard = []
    current_row = []
    
    # Создаем кнопки
    for time in sorted_times:
        current_row.append(
            InlineKeyboardButton(
                text=time,
                callback_data=f"end_time:{time}"
            )
        )
        
        # Формируем ряды по 3 кнопки
        if len(current_row) == 3:
            keyboard.append(current_row)
            current_row = []
    
    # Добавляем оставшиеся кнопки
    if current_row:
        keyboard.append(current_row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 