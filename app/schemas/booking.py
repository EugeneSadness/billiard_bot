from datetime import datetime, date, time
from pydantic import BaseModel, Field
from enum import Enum

class BookingStatus(str, Enum):
    ACTIVE = 'active'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'

class BookingBase(BaseModel):
    table_id: int
    client_name: str
    client_phone: str
    booking_date: date
    start_time: time
    end_time: time

class BookingCreate(BookingBase):
    client_id: int | None = None

class BookingUpdate(BaseModel):
    status: BookingStatus | None = None
    booking_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None

class BookingResponse(BookingBase):
    id: int
    created_at: datetime
    status: BookingStatus = Field(default=BookingStatus.ACTIVE)
    table_name: str | None = None 

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            time: lambda v: v.isoformat()
        }

class BookingFilter(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    status: BookingStatus | None = None
    table_id: int | None = None
    client_phone: str | None = None 