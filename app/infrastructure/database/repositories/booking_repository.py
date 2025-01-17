from datetime import datetime, date, time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.infrastructure.database.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingFilter, BookingStatus

class BookingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_booking(self, booking: BookingCreate) -> Booking:
        db_booking = Booking(
            table_id=booking.table_id,
            client_name=booking.client_name,
            client_phone=booking.client_phone,
            booking_date=booking.booking_date,
            start_time=booking.start_time,
            end_time=booking.end_time,
            status=BookingStatus.ACTIVE
        )
        self.session.add(db_booking)
        await self.session.commit()
        await self.session.refresh(db_booking)
        return db_booking

    async def get_bookings(self, filters: BookingFilter) -> list[Booking]:
        query = (
            select(Booking)
            .options(selectinload(Booking.table))
        )
        
        conditions = []
        
        if filters.client_phone:
            conditions.append(Booking.client_phone == filters.client_phone)
            
        if filters.date_from:
            conditions.append(Booking.booking_date >= filters.date_from)
            
        if filters.date_to:
            conditions.append(Booking.booking_date <= filters.date_to)
            
        if filters.status:
            conditions.append(Booking.status == filters.status)
            
        if filters.table_id:
            conditions.append(Booking.table_id == filters.table_id)
            
        if conditions:
            query = query.where(and_(*conditions))
            
        query = query.order_by(Booking.booking_date, Booking.start_time)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_booking(self, booking_id: int) -> Booking | None:
        return await self.session.get(Booking, booking_id)

    async def update_booking_status(
        self, 
        booking_id: int, 
        status: BookingStatus
    ) -> Booking | None:
        booking = await self.get_booking(booking_id)
        if booking:
            booking.status = status
            await self.session.commit()
            await self.session.refresh(booking)
        return booking

    async def check_table_availability(
        self, 
        table_id: int, 
        booking_date: date,
        start_time: time,
        end_time: time,
        exclude_booking_id: int | None = None
    ) -> bool:
        query = select(Booking).where(
            and_(
                Booking.table_id == table_id,
                Booking.booking_date == booking_date,
                Booking.status == BookingStatus.ACTIVE,
                Booking.start_time < end_time,
                Booking.end_time > start_time
            )
        )
        
        if exclude_booking_id:
            query = query.where(Booking.id != exclude_booking_id)
        
        result = await self.session.execute(query)
        return result.first() is None 