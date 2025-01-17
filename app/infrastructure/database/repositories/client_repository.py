from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.infrastructure.database.models.client import Client

class ClientRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_client(
        self,
        name: str,
        phone: str,
        visit_date: datetime
    ) -> Client:
        client = Client(
            name=name,
            phone=phone,
            visit_date=visit_date
        )
        self.session.add(client)
        await self.session.commit()
        return client

    async def get_client_by_phone(self, phone: str) -> Client | None:
        result = await self.session.execute(
            select(Client).where(Client.phone == phone)
        )
        return result.scalar_one_or_none()

    async def get_client(self, client_id: int) -> Client | None:
        return await self.session.get(Client, client_id)

    async def update_visit_date(self, client_id: int, visit_date: datetime) -> None:
        query = (
            update(Client)
            .where(Client.id == client_id)
            .values(visit_date=visit_date)
        )
        await self.session.execute(query)
        await self.session.commit() 