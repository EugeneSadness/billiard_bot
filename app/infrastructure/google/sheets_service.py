from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self, spreadsheet_id: str, credentials: Credentials):
        self.spreadsheet_id = spreadsheet_id
        self.service = build('sheets', 'v4', credentials=credentials)
        self.sheet = self.service.spreadsheets()

    async def get_sheet_data(self) -> list:
        result = self.sheet.values().get(
            spreadsheetId=self.spreadsheet_id,
            range='A1:O39'  # Увеличиваем диапазон для новой структуры
        ).execute()
        return result.get('values', [])
        
    async def get_available_dates(self) -> list:
        data = await self.get_sheet_data()
        available_dates = []
        
        if not data or len(data) < 3:  # Минимум нужны строки: время + 3 стола
            return available_dates
            
        # Получаем даты из первого столбца (пропускаем первые 3 строки с временем)
        for row_idx in range(3, len(data), 4):  # Шаг 4, так как каждая дата занимает 4 строки (по числу столов)
            date_cell = data[row_idx][0] if len(data[row_idx]) > 0 else None
            
            if not date_cell or not date_cell.strip():  # Пропускаем пустые ячейки
                continue
                
            try:
                # Парсим дату
                date = datetime.strptime(date_cell, '%d.%m')
                date = date.replace(year=datetime.now().year)
                
                # Проверяем наличие свободных слотов для этой даты
                has_free_slots = False
                for table_idx in range(4):  # Проверяем все 4 стола для этой даты
                    current_row = data[row_idx + table_idx]
                    if len(current_row) < 3:
                        has_free_slots = True
                        break
                    # Проверяем ячейки времени (начиная с индекса 1, пропуская название стола)
                    for time_idx in range(1, len(current_row)):
                        if current_row[time_idx].strip() == '' or len(current_row) < 15:
                            has_free_slots = True
                            break
                    if has_free_slots:
                        break
                
                if has_free_slots:
                    available_dates.append({
                        'date': date.strftime('%d.%m.%y'),
                        'weekday': date.strftime('%A')
                    })
                    
            except (ValueError, AttributeError) as e:
                logger.error(f"Error parsing date {date_cell}: {e}")
                continue
                
        return available_dates

    async def get_available_times(self, selected_date: str, table_preference: str = 'random') -> list:
        data = await self.get_sheet_data()
        available_times = []
        
        # Получаем строку с временем (первая строка)
        time_slots = data[0][2:14]  # Пропускаем первые две ячейки
        
        # Ищем индекс строки с выбранной датой
        date_row_idx = None
        for idx in range(3, len(data), 4):
            selected_date = selected_date.split('.')[0] + '.' + selected_date.split('.')[1]
            if data[idx][0].strip() == selected_date:
                date_row_idx = idx
                break
            
        if date_row_idx is None:
            return available_times
            
        # Проверяем доступность каждого временного слота
        for time_idx, time_slot in enumerate(time_slots, start=2):
            if table_preference == 'random':
                # Проверяем все столы
                has_free_tables = False
                for table_idx in range(4):
                    current_row = data[date_row_idx + table_idx]
                    if len(current_row) <= time_idx or current_row[time_idx].strip() == '':
                        has_free_tables = True
                        break
                if has_free_tables:
                    available_times.append(time_slot)
            else:
                # Проверяем только выбранный стол
                table_idx = int(table_preference) - 1
                current_row = data[date_row_idx + table_idx]
                if len(current_row) <= time_idx or current_row[time_idx].strip() == '':
                    available_times.append(time_slot)
                
        return available_times
    

    async def get_best_table_and_end_times(self, date_str: str, start_time: str) -> tuple[int, list[str]]:
        data = await self.get_sheet_data()
        
        # Находим индекс строки с нужной датой
        target_date = datetime.strptime(date_str, '%d.%m.%y')
        target_row_idx = None
        
        for idx in range(3, len(data), 4):  # Начинаем с 4-й строки, шаг 4 (каждая дата = 4 строки)
            try:
                date_cell = data[idx][0]  # Дата в первом столбце
                if date_cell:
                    row_date = datetime.strptime(date_cell, '%d.%m')
                    if (row_date.day == target_date.day and 
                        row_date.month == target_date.month):
                        target_row_idx = idx
                        break
            except (ValueError, IndexError):
                continue
        
        if target_row_idx is None:
            return None, []

        # Находим индекс колонки с начальным временем
        time_slots = data[0][2:]  # Пропускаем первую ячейку (пустая или "Время")
        target_col_idx = None
        
        for idx, time_slot in enumerate(time_slots, start=2):
            if time_slot == start_time:
                target_col_idx = idx
                break

        if target_col_idx is None:
            return None, []

        available_tables = []  # список кортежей (номер_стола, количество_доступных_часов)
        
        # Проверяем каждый стол для выбранной даты
        for table_idx in range(4):
            current_row_idx = target_row_idx + table_idx
            
            # Проверяем, свободен ли стол в начальное время
            is_table_free = True 
            if current_row_idx < len(data):
                if target_col_idx < len(data[current_row_idx]):
                    if data[current_row_idx][target_col_idx].strip() != '':
                        is_table_free = False
            if is_table_free:
                consecutive_hours = 0
                # Проверяем последующие временные слоты
                for col_idx in range(target_col_idx, len(time_slots) + 2):
                    if (len(data[current_row_idx]) <= col_idx or data[current_row_idx][col_idx] == ''):
                        consecutive_hours += 1
                    else:
                        break
                
                available_tables.append((table_idx+1, consecutive_hours))
        
        if not available_tables:
            return None, []
        
        # Выбираем стол с максимальным временем бронирования
        best_table, max_hours = max(available_tables, key=lambda x: x[1])
        # Формируем список доступных времен окончания для выбранного стола
        available_end_times = []
        for i in range(0, max_hours):
            if target_col_idx + i < len(time_slots) + 1:
                available_end_times.append(time_slots[target_col_idx + i - 1])
        
        return best_table, available_end_times 


    async def update_booking_in_sheets(
        self, 
        date_str: str, 
        start_time: str, 
        end_time: str, 
        table_id: int,
        client_name: str,
        client_phone: str
    ) -> bool:
        try:
            data = await self.get_sheet_data()
            
            # Находим индекс строки с нужной датой
            target_date = datetime.strptime(date_str, '%d.%m.%y')
            target_row_idx = None
            
            for idx in range(3, len(data), 4):
                try:
                    date_cell = data[idx][0]
                    if date_cell:
                        row_date = datetime.strptime(date_cell, '%d.%m')
                        if (row_date.day == target_date.day and 
                            row_date.month == target_date.month):
                            target_row_idx = idx
                            break
                except (ValueError, IndexError):
                    continue
            
            if target_row_idx is None:
                return False

            # Находим индексы колонок для начального и конечного времени
            time_slots = data[0][2:]
            start_col_idx = None
            end_col_idx = None
            
            for idx, time_slot in enumerate(time_slots, start=3):
                if time_slot == start_time:
                    start_col_idx = idx
                elif time_slot == end_time:
                    end_col_idx = idx
                    break

            if start_col_idx is None or end_col_idx is None:
                return False

            # Формируем значение для ячейки (имя и телефон)
            cell_value = f"{client_name}\n{client_phone}"
            
            # Определяем диапазон ячеек для обновления
            row_idx = target_row_idx + (table_id - 1)  # -1 так как table_id начинается с 1
            range_start = f"{self._column_letter(start_col_idx)}{row_idx + 1}"
            range_end = f"{self._column_letter(end_col_idx)}{row_idx + 1}"
            range_name = f"{range_start}:{range_end}"

            # Подготавливаем данные для обновления
            values = [[cell_value] * (end_col_idx - start_col_idx + 1)]
            
            # Обновляем ячейки, сохраняя форматирование
            self.sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                includeValuesInResponse=True,
                body={'values': values}
            ).execute()

            return True
            
        except Exception as e:
            logger.error(f"Error updating booking in sheets: {e}")
            return False

    def _column_letter(self, column_number: int) -> str:
        """Преобразует номер столбца в буквенное обозначение (1 -> A, 2 -> B, etc.)"""
        result = ""
        while column_number > 0:
            column_number -= 1
            result = chr(65 + (column_number % 26)) + result
            column_number //= 26
        return result

    async def clear_booking_in_sheets(
        self, 
        date_str: str, 
        start_time: str, 
        end_time: str, 
        table_id: int
    ) -> bool:
        try:
            data = await self.get_sheet_data()
            
            # Находим индекс строки с нужной датой
            target_date = datetime.strptime(date_str, '%d.%m.%y')
            target_row_idx = None
            
            for idx in range(3, len(data), 4):
                try:
                    date_cell = data[idx][0]
                    if date_cell:
                        row_date = datetime.strptime(date_cell, '%d.%m')
                        if (row_date.day == target_date.day and 
                            row_date.month == target_date.month):
                            target_row_idx = idx + (table_id - 1)
                            break
                except (ValueError, IndexError):
                    continue
            
            if target_row_idx is None:
                return False

            # Нормализуем форматы времени
            def normalize_time(time_str: str) -> str:
                try:
                    # Преобразуем строку времени в объект time и обратно в строку
                    time_obj = datetime.strptime(time_str, '%H:%M').time()
                    return time_obj.strftime('%-H:%M')  # %-H уберет ведущий ноль
                except ValueError:
                    return time_str

            # Находим индексы колонок для начального и конечного времени
            time_slots = data[0][2:]
            start_col_idx = None
            end_col_idx = None
            
            normalized_end_time = normalize_time(end_time)
            normalized_start_time = normalize_time(start_time)
            
            for idx, time_slot in enumerate(time_slots, start=3):
                normalized_slot = normalize_time(time_slot)
                if normalized_slot == normalized_start_time:
                    start_col_idx = idx
                elif normalized_slot == normalized_end_time:
                    end_col_idx = idx
                    break
                
            if start_col_idx is None or end_col_idx is None:
                return False
            
            # Очищаем ячейки
            range_name = f"{self._column_letter(start_col_idx)}{target_row_idx + 1}:{self._column_letter(end_col_idx)}{target_row_idx + 1}"
            
            # Используем пустые значения для очистки ячеек
            self.sheet.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                includeValuesInResponse=True,
                body={'values': [['']*((end_col_idx - start_col_idx) + 1)]}
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing booking in sheets: {e}")
            return False

    async def block_day_in_sheets(self, date_str: str) -> bool:
        try:
            data = await self.get_sheet_data()
            
            # Находим индекс строки с нужной датой
            target_date = datetime.strptime(date_str, '%d.%m.%y')
            target_row_idx = None
            
            for idx in range(3, len(data), 4):
                try:
                    date_cell = data[idx][0]
                    if date_cell:
                        row_date = datetime.strptime(date_cell, '%d.%m')
                        if (row_date.day == target_date.day and 
                            row_date.month == target_date.month):
                            target_row_idx = idx
                            break
                except (ValueError, IndexError):
                    continue
            
            if target_row_idx is None:
                return False

            # Заполняем все ячейки для всех столов на этот день
            for table_idx in range(4):
                row_idx = target_row_idx + table_idx
                range_name = f"C{row_idx + 1}:O{row_idx + 1}"  # От C до O (все временные слоты)
                
                # Используем "BLOCKED" для всех ячеек
                self.sheet.values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    includeValuesInResponse=True,
                    body={'values': [['BLOCKED'] * 13]}  # 13 временных слотов
                ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error blocking day in sheets: {e}")
            return False

    async def unblock_day_in_sheets(self, date_str: str) -> bool:
        try:
            data = await self.get_sheet_data()
            
            # Находим индекс строки с нужной датой
            target_date = datetime.strptime(date_str, '%d.%m.%y')
            target_row_idx = None
            
            for idx in range(3, len(data), 4):
                try:
                    date_cell = data[idx][0]
                    if date_cell:
                        row_date = datetime.strptime(date_cell, '%d.%m')
                        if (row_date.day == target_date.day and 
                            row_date.month == target_date.month):
                            target_row_idx = idx
                            break
                except (ValueError, IndexError):
                    continue
            
            if target_row_idx is None:
                return False

            # Очищаем все ячейки для всех столов на этот день
            for table_idx in range(4):
                row_idx = target_row_idx + table_idx
                range_name = f"C{row_idx + 1}:O{row_idx + 1}"  # От C до O (все временные слоты)
                
                # Используем пустые значения для очистки ячеек
                self.sheet.values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    includeValuesInResponse=True,
                    body={'values': [['']*13]}  # 13 пустых временных слотов
                ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error unblocking day in sheets: {e}")
            return False

    async def get_available_end_times_for_table(self, date_str: str, start_time: str, table_id: int) -> list[str]:
        data = await self.get_sheet_data()
        
        # Ищем строку для выбранной даты и стола
        target_date = datetime.strptime(date_str, '%d.%m.%y')
        target_row_idx = None
        
        for idx in range(3, len(data), 4):
            try:
                date_cell = data[idx][0]
                if date_cell:
                    row_date = datetime.strptime(date_cell, '%d.%m')
                    if (row_date.day == target_date.day and 
                        row_date.month == target_date.month):
                        target_row_idx = idx + (table_id - 1)  # Корректируем для конкретного стола
                        break
            except (ValueError, IndexError):
                continue
            
        if target_row_idx is None:
            return []

        # Ищем колонку времени начала
        time_slots = data[0][2:]
        start_col_idx = None
        
        for idx, time_slot in enumerate(time_slots, start=2):
            if time_slot == start_time:
                start_col_idx = idx
                break
            
        if start_col_idx is None:
            return []

        # Проверяем последовательные доступные слоты
        available_end_times = []
        current_row = data[target_row_idx]
        
        for col_idx in range(start_col_idx, len(time_slots) + 2):
            if col_idx >= len(current_row) or current_row[col_idx].strip() == '':
                if col_idx - 1 < len(time_slots):
                    available_end_times.append(time_slots[col_idx - 1])
            else:
                break
            
        return available_end_times
