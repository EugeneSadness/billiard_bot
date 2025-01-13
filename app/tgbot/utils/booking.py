from datetime import datetime, timedelta

def get_available_dates():
    # Заглушка для демонстрации
    dates = []
    current_date = datetime.now()
    for i in range(7):
        date = current_date + timedelta(days=i)
        dates.append({
            'date': date.strftime('%d.%m.%y'),
            'weekday': date.strftime('%a')[:2].upper()
        })
    return dates

def get_available_times(date):
    # Заглушка для демонстрации
    return ["11:00","12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00","19:00", "20:00", "21:00", "22:00"]
