import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from alembic import command
from alembic.config import Config
from sqlalchemy.sql import text
from google.oauth2.credentials import Credentials

from app.tgbot.handlers.booking import booking_router
from app.tgbot.middlewares.database import DatabaseMiddleware
from app.tgbot.middlewares.google_sheets import GoogleSheetsMiddleware
from config.config import settings
from app.infrastructure.google.sheets_service import GoogleSheetsService

logger = logging.getLogger(__name__)

async def create_db_session():
    # Создаем URL для подключения к БД
    database_url = (
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres.host}:{settings.postgres.port}/{settings.postgres.name}"
    )
    
    # Создаем движок SQLAlchemy
    engine = create_async_engine(
        database_url,
        echo=settings.debug,  # SQL логи в режиме отладки
        pool_size=5,
        max_overflow=10
    )
    
    # Создаем фабрику сессий
    async_session = async_sessionmaker(
        engine,
        expire_on_commit=False
    )
    
    return async_session

async def main():
    try:
        # Создаем фабрику сессий БД
        async_session = await create_db_session()
        
        # Пробуем подключиться к БД
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            logger.info("Database connection successful")
        
        # Применяем миграции
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations applied successfully")
        
        # Инициализация бота
        bot = Bot(token=settings.bot_token)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Инициализация Google Sheets
        credentials = Credentials.from_service_account_file(
            'path/to/credentials.json',
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        sheets_service = GoogleSheetsService(
            spreadsheet_id=settings.google_spreadsheet_id,
            credentials=credentials
        )
        
        # Регистрируем middleware
        dp.update.middleware(DatabaseMiddleware(async_session))
        dp.update.middleware(GoogleSheetsMiddleware(sheets_service))
        dp.include_router(booking_router)
        
        logger.info("Starting bot")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.exception("Error during startup: %s", e)
        raise
    finally:
        if 'bot' in locals():
            await bot.session.close()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Запускаем бота
    asyncio.run(main())