from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.infrastructure.database.models.booking import Booking
from app.tgbot.utils.date_helpers import format_date_with_weekday

def get_main_menu_inline_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Забронировать столик 🎱",
        callback_data="start_booking"
    )
    builder.button(
        text="Мои брони 📅",
        callback_data="my_bookings"
    )
    builder.button(
        text="Отменить бронь ❌",
        callback_data="cancel_booking"
    )
    builder.adjust(1)  # По одной кнопке в ряд
    return builder.as_markup()

def get_dates_keyboard(available_dates: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for date in available_dates:
        # Используем helper для форматирования даты и получения русского названия дня недели
        date_str = date['date'][:5]  # Берем только dd.mm
        _, weekday_ru = format_date_with_weekday(date['date'])  # Получаем русское название дня недели
        
        builder.button(
            text=f"{date_str} ({weekday_ru.capitalize()})",  # Капитализируем первую букву дня недели
            callback_data=f"date_{date['date']}"
        )
    
    builder.button(
        text="« Назад в меню",
        callback_data="back_to_main"
    )
    
    builder.adjust(2)  
    return builder.as_markup()

def sort_time(time: str) -> int:
    """
    Вспомогательная функция для сортировки времени.
    Преобразует время в минуты, при этом для времени после полуночи добавляет 24 часа
    """
    hour = int(time.split(':')[0])
    # Если час между 0 и 3, добавляем 24 часа для правильной сортировки
    if 0 <= hour <= 3:
        hour += 24
    return hour

def get_time_keyboard(available_times: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Сортируем времена с учетом перехода через полночь
    sorted_times = sorted(available_times, key=sort_time)
    
    for time in sorted_times:
        builder.button(
            text=f"{time}",
            callback_data=f"time:{time}"
        )
    
    builder.button(
        text="« Назад к выбору даты",
        callback_data="back_to_dates"
    )
    
    builder.adjust(3)  # По три времени в ряд
    return builder.as_markup()

def get_end_time_keyboard(available_end_times: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Используем ту же логику сортировки для времени окончания
    sorted_times = sorted(available_end_times, key=sort_time)
    
    for time in sorted_times:
        builder.button(
            text=f"{time}",
            callback_data=f"end_time:{time}"
        )
    
    builder.button(
        text="« Назад к выбору времени",
        callback_data="back_to_start_time"
    )
    
    builder.adjust(3)  # По три времени в ряд
    return builder.as_markup() 

def get_cancel_booking_keyboard(bookings: list[Booking]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for booking in bookings:
        date_str, weekday_ru = format_date_with_weekday(booking.booking_date.strftime('%d.%m.%y'))
        button_text = (
            f"{date_str} ({weekday_ru}) "
            f"{booking.start_time.strftime('%H:%M')}-{booking.end_time.strftime('%H:%M')}"
        )
        builder.button(
            text=button_text,
            callback_data=f"cancel_booking:{booking.id}"
        )
    
    builder.button(
        text="« Назад в меню",
        callback_data="back_to_main"
    )
    
    builder.adjust(1)
    return builder.as_markup() 