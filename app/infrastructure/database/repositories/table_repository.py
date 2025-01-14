from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.infrastructure.database.models.table import Table

class TableRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_tables(self):
        result = await self.session.execute(select(Table))
        return result.scalars().all()

    async def get_table(self, table_id: int):
        return await self.session.get(Table, table_id) 