from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class GoogleSheetsService:
    def __init__(self, spreadsheet_id: str, credentials: Credentials):
        self.spreadsheet_id = spreadsheet_id
        self.service = build('sheets', 'v4', credentials=credentials)
        self.sheet = self.service.spreadsheets()

    async def get_sheet_data(self) -> list:
        result = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range='A1:Z55'  # 1 строка заголовка + (13 часов × 4 стола) + небольшой запас
        ).execute()
        return result.get('values', [])
        
    async def get_available_dates(self) -> list:
        data = await self.get_sheet_data()
        available_dates = []
        
        if not data or len(data) < 2:
            return available_dates
            
        # Получаем заголовки с датами (начиная с 3-го столбца - индекс 2)
        headers = data[0][2:]  # Пропускаем 'Время', 'Столы'
        
        for col_idx, date_str in enumerate(headers, start=2):
            if not date_str:  # Пропускаем пустые заголовки
                continue
                
            try:
                # Парсим дату из заголовка
                date = datetime.strptime(date_str, '%d.%m')
                date = date.replace(year=datetime.now().year)
                
                # Проверяем, есть ли свободные слоты в этой колонке
                has_free_slots = False
                for row in data[1:]:  # Пропускаем заголовок
                    if len(row) <= col_idx or (len(row) > col_idx and not row[col_idx].strip()):
                        has_free_slots = True
                        break
                
                if has_free_slots:
                    available_dates.append({
                        'date': date.strftime('%d.%m.%y'),
                        'weekday': date.strftime('%a')[:2].upper()
                    })
                    
            except ValueError:
                continue  # Пропускаем неверный формат даты
        
        return available_dates
    
    async def get_available_times(self, date_str: str) -> list:
        data = await self.get_sheet_data()
        available_times = []
        
        if not data or len(data) < 2:
            return available_times
            
        # Находим индекс колонки с нужной датой
        headers = data[0]
        target_date = datetime.strptime(date_str, '%d.%m.%y')
        target_col_idx = None
        
        # Начинаем с 3-го столбца (индекс 2), пропуская 'Время', 'Столы'
        for idx, header in enumerate(headers[2:], start=2):
            try:
                if header:
                    header_date = datetime.strptime(header, '%d.%m')
                    if (header_date.day == target_date.day and 
                        header_date.month == target_date.month):
                        target_col_idx = idx
                        break
            except ValueError:
                continue
        
        if target_col_idx is not None:
            # Проходим по строкам с шагом 4 (каждый временной слот)
            for i in range(3, len(data), 4):
                if i + 4 > len(data):  # Проверяем, что хватает строк для полного блока
                    break
                    
                time_block = data[i:i+4]  # Берем блок из 4 строк
                time = time_block[0][0]  # Время всегда в первой строке блока
                
                # Проверяем наличие свободных столов в этом временном блоке
                has_free_tables = False
                for row in time_block:
                    # Если строка короче, чем целевой индекс - значит слот свободен
                    if len(row) <= target_col_idx:
                        has_free_tables = True
                        break
                
                if has_free_tables:
                    available_times.append(time)
        
        return sorted(available_times)

    async def book_time(self, date: str, time: str, name: str) -> bool:
        # TODO: Реализовать бронирование времени
        pass 