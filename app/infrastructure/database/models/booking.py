from datetime import datetime
from pydantic import BaseModel

class Booking(BaseModel):
    user_id: int
    name: str
    date: datetime
    start_time: str
    end_time: str
    phone: str
