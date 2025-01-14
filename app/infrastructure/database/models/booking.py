from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Time, Date
from sqlalchemy.orm import relationship
from app.infrastructure.database.models.base import Base

class Booking(Base):
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    table_id = Column(Integer, ForeignKey('tables.id'))
    client_id = Column(Integer, ForeignKey('clients.id'))
    client_name = Column(String(100), nullable=False)
    client_phone = Column(String(20), nullable=False)
    booking_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default='CURRENT_TIMESTAMP')
    status = Column(String(20), default='active')

    table = relationship("Table", back_populates="bookings")
    client = relationship("Client", back_populates="bookings")