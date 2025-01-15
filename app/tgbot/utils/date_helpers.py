from datetime import datetime

WEEKDAYS_RU = {
    'monday': 'понедельник',
    'tuesday': 'вторник',
    'wednesday': 'среда',
    'thursday': 'четверг',
    'friday': 'пятница',
    'saturday': 'суббота',
    'sunday': 'воскресенье'
}

def format_date_with_weekday(date_str: str, date_format: str = '%d.%m.%y') -> tuple[str, str]:
    """
    Преобразует строку даты в кортеж (дата, день недели на русском)
    
    Args:
        date_str: Строка с датой
        date_format: Формат даты для парсинга
    
    Returns:
        tuple: (дата в исходном формате, день недели на русском)
    """
    date_obj = datetime.strptime(date_str, date_format)
    weekday = date_obj.strftime('%A').lower()
    return date_str, WEEKDAYS_RU[weekday] 