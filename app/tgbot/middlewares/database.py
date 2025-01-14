import logging

from typing import Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Update
from psycopg import Error
from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.repositories.booking_repository import BookingRepository
from app.infrastructure.database.repositories.table_repository import TableRepository
from app.infrastructure.database.repositories.client_repository import ClientRepository

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, async_session_maker):
        self.async_session_maker = async_session_maker
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, any]], Awaitable[None]],
        event: Update,
        data: dict[str, any]
    ) -> any:
        async with self.async_session_maker() as session:
            data['session'] = session
            data['booking_repository'] = BookingRepository(session)
            data['table_repository'] = TableRepository(session)
            data['client_repository'] = ClientRepository(session)
            
            return await handler(event, data)
