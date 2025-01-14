from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, time

class GoogleSheetsService:
    def __init__(self, spreadsheet_id: str, credentials: Credentials):
        self.spreadsheet_id = spreadsheet_id
        self.service = build('sheets', 'v4', credentials=credentials)
        self.sheet = self.service.spreadsheets()

    def _get_column_letter(self, time_slot: time) -> str:
        """Преобразует время в букву колонки"""
        # Начинаем с 15:00 (колонка B)
        base_hour = 15
        current_hour = time_slot.hour
        
        if current_hour < base_hour:
            current_hour += 24
        
        column_index = current_hour - base_hour + 1
        return chr(65 + column_index)  # A=65 в ASCII

    async def add_booking(self, booking_data: dict) -> bool:
        try:
            # Преобразуем дату в номер строки (каждая строка = день)
            booking_date = datetime.strptime(booking_data['date'], '%d.%m.%y')
            row = booking_date.day + 1  # +1 потому что первая строка - заголовок

            # Получаем букву колонки из времени начала
            column = self._get_column_letter(booking_data['start_time'])
            
            # Формируем диапазон ячейки (например, B2)
            cell_range = f"{column}{row}"
            
            # Формируем текст для записи
            value = f"{booking_data['client_name']}\n{booking_data['phone']}"

            # Записываем данные
            self.sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=cell_range,
                valueInputOption='RAW',
                body={'values': [[value]]}
            ).execute()

            return True
        except Exception as e:
            print(f"Error updating sheet: {e}")
            return False 