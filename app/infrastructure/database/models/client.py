from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class Client(BaseModel):
    id: Optional[int] = None
    visit_date: datetime
    name: str
    phone: str

    class Config:
        orm_mode = True
        from_attributes = True
