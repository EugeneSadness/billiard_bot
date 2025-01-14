from datetime import datetime
from pydantic import BaseModel

class ClientSchema(BaseModel):
    id: int | None = None
    name: str
    phone: str
    visit_date: datetime

    class Config:
        from_attributes = True 