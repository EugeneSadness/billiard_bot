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
            for i in range(3, len(data), 4):
                if i + 4 > len(data):  
                    break
                    
                time_block = data[i:i+4]  
                time = time_block[0][0]  
                
                # Проверяем наличие свободных столов в этом временном блоке
                has_free_tables = False
                for row in time_block:
                    if len(row) <= target_col_idx:
                        has_free_tables = True
                        break

                    else:
                        if row[target_col_idx] == '':
                            has_free_tables = True
                            break
                
                if has_free_tables:
                    available_times.append(time)
        
        return sorted(available_times)

    async def book_time(self, date: str, time: str, name: str) -> bool:
        # TODO: Реализовать бронирование времени
        pass 

    async def get_available_end_times(self, date_str: str, start_time: str) -> list[str]:
        data = await self.get_sheet_data()
        available_end_times = []
        
        if not data or len(data) < 2:
            return available_end_times
            
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
            # Находим индекс строки с начальным временем
            start_row_idx = None
            for i in range(3, len(data), 4):
                if i + 4 > len(data):
                    break
                
                time_block = data[i:i+4]
                if time_block[0][0] == start_time:
                    start_row_idx = i
                    break
                print(f"time_block: {time_block[0][0]}, start_time: {start_time}")
            
            if start_row_idx is not None:
                # Проверяем последующие временные блоки
                for i in range(start_row_idx + 4, len(data), 4):
                    if i + 4 > len(data):
                        break
                    
                    time_block = data[i:i+4]
                    time = time_block[0][0]
                    
                    # Проверяем наличие свободных столов в этом временном блоке
                    has_free_tables = False
                    for row in time_block:
                        if len(row) <= target_col_idx:
                            has_free_tables = True
                            break
                    
                    if not has_free_tables:
                        break
                    
                    available_end_times.append(time)
                    
                    # Ограничение максимального времени (до 03:00)
                    current_hour = int(time.split(':')[0])
                    if current_hour > 3 and current_hour < 12:
                        break
            
        return available_end_times 

    async def get_best_table_and_end_times(self, date_str: str, start_time: str) -> tuple[int, list[str]]:
        data = await self.get_sheet_data()
        if not data or len(data) < 2:
            return None, []
        
        # Находим индекс колонки с нужной датой
        headers = data[0]
        target_date = datetime.strptime(date_str, '%d.%m.%y')
        target_col_idx = None
        
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
        
        print(f"target_col_idx: {target_col_idx}")
        if target_col_idx is None:
            return None, []

        # Находим блок с начальным временем
        start_row_idx = None
        for i in range(3, len(data), 4):
            if i + 4 > len(data):
                break
            
            time_block = data[i:i+4]
            if time_block[0][0] == start_time:
                start_row_idx = i
                break

        print(f"start_row_idx: {start_row_idx}")
        if start_row_idx is None:
            return None, []

        available_tables = []  # список кортежей (номер_стола, количество_доступных_часов)
        # Проверяем каждый стол (4 строки в блоке)
        for table_idx in range(4):
            consecutive_hours = 0
            current_row_idx = start_row_idx + table_idx
            print(f"current_row_idx: {current_row_idx}")

            # Проверяем последующие временные блоки для этого стола
            row_offset = current_row_idx - start_row_idx  # смещение для конкретного стола
            
            # Проверяем, свободен ли стол в начальное время
            is_table_free = False
            if len(data[current_row_idx]) <= target_col_idx:
                is_table_free = True
            elif data[current_row_idx][target_col_idx] == '':
                is_table_free = True
            
            if is_table_free:
                # Считаем, сколько последовательных часов доступно
                for i in range(start_row_idx + 4, len(data), 4):
                    if i + row_offset >= len(data):
                        break
                    
                    if len(data[i + row_offset]) <= target_col_idx:
                        consecutive_hours += 1
                    elif data[i + row_offset][target_col_idx] == '':
                        consecutive_hours += 1
                    else:
                        break
                    
                    # Проверяем ограничение времени (до 03:00)
                    time = data[i][0]
                    current_hour = int(time.split(':')[0])
                    if current_hour > 3 and current_hour < 12:
                        break
                
                available_tables.append((table_idx + 1, consecutive_hours))
        
        if not available_tables:
            return None, []
        
        # Выбираем стол с максимальным временем бронирования
        best_table, max_hours = max(available_tables, key=lambda x: x[1])
        
        # Формируем список доступных времен окончания для выбранного стола
        available_end_times = []
        for i in range(1, max_hours + 1):
            row_idx = start_row_idx + (i * 4)
            if row_idx < len(data):
                available_end_times.append(data[row_idx][0])
        
        return best_table, available_end_times 