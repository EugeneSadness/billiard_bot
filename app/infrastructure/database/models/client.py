from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.infrastructure.database.models.base import Base

class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    visit_date = Column(DateTime(timezone=True), nullable=False)
    
    bookings = relationship("Booking", back_populates="client")
