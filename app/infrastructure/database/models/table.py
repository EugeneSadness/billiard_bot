from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.infrastructure.database.models.base import Base

class Table(Base):
    __tablename__ = 'tables'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    
    bookings = relationship("Booking", back_populates="table")