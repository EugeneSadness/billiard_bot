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
    builder.button(
        text="Как пройти к нам 🗺️",
        callback_data="how_to_find_us"
    )
    builder.button(
        text="Контактная информация ℹ️",
        callback_data="contact_info"
    )
    builder.adjust(1)  # По одной кнопке в ряд
    return builder.as_markup()

def get_dates_keyboard(available_dates: list, is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for date in available_dates:
        date_str = date['date'][:5]
        _, weekday_ru = format_date_with_weekday(date['date'])
        
        builder.button(
            text=f"{date_str} ({weekday_ru.capitalize()})",
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

def get_time_keyboard(available_times: list, is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
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
    
    builder.adjust(3)
    return builder.as_markup()

def get_end_time_keyboard(available_end_times: list[str], is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
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
    
    builder.adjust(3)
    return builder.as_markup()

def get_cancel_booking_keyboard(bookings: list[Booking], is_admin: bool = False) -> InlineKeyboardMarkup:
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

def get_admin_menu_inline_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Забронировать столик 🎱",
        callback_data="start_booking"
    )
    builder.button(
        text="Заблокировать день 🚫",
        callback_data="block_day"
    )
    builder.button(
        text="Разблокировать день 🔓",
        callback_data="unblock_day"
    )
    builder.button(
        text="Управление бронями 👥",
        callback_data="manage_bookings"
    )
    builder.adjust(1)  # По одной кнопке в ряд
    return builder.as_markup()

def get_all_bookings_keyboard(bookings: list[Booking]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for booking in bookings:
        date_str, weekday_ru = format_date_with_weekday(booking.booking_date.strftime('%d.%m.%y'))
        
        button_text = (
            f"{booking.client_name} {date_str}\n"
            f"{booking.start_time.strftime('%H:%M')}-{booking.end_time.strftime('%H:%M')}"
        )
        builder.button(
            text=button_text,
            callback_data=f"admin_cancel:{booking.id}"
        )
    
    builder.button(
        text="« Назад в меню",
        callback_data="back_to_main"
    )
    
    builder.adjust(1)
    return builder.as_markup()

def get_back_to_admin_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="« Назад в админ-меню",
        callback_data="back_to_main"
    )
    builder.adjust(1)
    return builder.as_markup()

def get_table_preference_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Порядок кнопок соответствует предпочтениям пользователя
    builder.button(
        text="Любой стол 🎱",
        callback_data="table_pref:random"
    )
    builder.button(
        text="Красный стол ❤️",
        callback_data="table_pref:4"
    )
    builder.button(
        text="Зелёный стол 💚",
        callback_data="table_pref:3"
    )
    builder.button(
        text="Леопардовый стол 🐆",
        callback_data="table_pref:1"
    )
    builder.button(
        text="Синий стол 💙",
        callback_data="table_pref:2"
    )
    
    builder.button(
        text="« Назад к выбору даты",
        callback_data="back_to_dates"
    )
    
    builder.adjust(1)  # По одной кнопке в ряд
    return builder.as_markup() 