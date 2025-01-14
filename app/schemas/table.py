from pydantic import BaseModel

class TableSchema(BaseModel):
    id: int | None = None
    name: str
    
    class Config:
        from_attributes = True