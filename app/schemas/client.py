from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re
from config.config import settings

class ClientCreate(BaseModel):
    id: int | None = None
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=11, max_length=12)
    visit_date: datetime | None = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        # Удаляем лишние пробелы
        value = ' '.join(value.split())
        
        # Проверка на админское имя
        if value == settings.ADMIN_NAME:
            return value
            
        # Проверяем, что имя содержит только буквы и пробелы
        if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s]+$', value):
            raise ValueError('Имя должно содержать только буквы')
        return value

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, value: str) -> str:
        # Удаляем все пробелы и дефисы
        phone = re.sub(r'[\s-]', '', value)
        
        # Проверяем формат номера
        if not re.match(r'^(?:\+7|8)\d{10}$', phone):
            raise ValueError('Неверный формат номера телефона. Используйте +7 или 8 и 10 цифр')
        
        # Преобразуем все номера к формату +7
        if phone.startswith('8'):
            phone = '+7' + phone[1:]
            
        return phone

    class Config:
        from_attributes = True 