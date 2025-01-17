from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from config.config import settings

class IsAdmin(BaseFilter):
    def __init__(self):
        pass

    async def __call__(
        self, 
        event: Message | CallbackQuery, 
        state: FSMContext
    ) -> bool:
        # Получаем данные из state
        user_data = await state.get_data()
        return user_data.get('is_admin', False) 