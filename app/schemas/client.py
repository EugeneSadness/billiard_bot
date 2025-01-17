from datetime import datetime
from pydantic import BaseModel

class ClientCreate(BaseModel):
    id: int | None = None
    name: str
    phone: str
    visit_date: datetime | None = None

    class Config:
        from_attributes = True 