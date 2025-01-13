from datetime import datetime
from pydantic import BaseModel

class Reservation(BaseModel):
    client_id: int
    table_id: int
    start_time: datetime
    end_time: datetime
