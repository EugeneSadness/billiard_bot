import asyncio
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine
from app.infrastructure.database.models.base import Base

from alembic import context
from config.config import settings
# from sqlalchemy.engine import Connection

# Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata object for autogenerate support (if needed, otherwise None)
target_metadata = Base.metadata

# Database URL for SQLAlchemy
url = f"postgresql+psycopg://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres.host}:{settings.postgres.port}/{settings.postgres_db}"
engine = create_async_engine(url)


async def run_migrations():
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)


def do_run_migrations(connection: AsyncConnection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


asyncio.run(run_migrations())
