"""Create booking tables

Revision ID: create_booking_tables
Revises: b20e5643d3bd
Create Date: 2024-01-24
"""
from typing import Sequence, Union
from alembic import op

revision: str = 'create_booking_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Создаем таблицу столов
    op.execute("""
        CREATE TABLE IF NOT EXISTS tables (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL
        );
    """)
    
    # Добавляем начальные данные
    op.execute("""
        INSERT INTO tables (name) VALUES
        ('леопардовый'),
        ('синий'),
        ('зеленый'),
        ('красный');
    """)
    
    # Создаем таблицу бронирований
    op.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            table_id INTEGER REFERENCES tables(id),
            client_name VARCHAR(100) NOT NULL,
            client_phone VARCHAR(20) NOT NULL,
            booking_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active'
        );
    """)
    
    # Добавляем индексы для оптимизации поиска
    op.execute("""
        CREATE INDEX idx_bookings_date ON bookings(booking_date);
        CREATE INDEX idx_bookings_status ON bookings(status);
    """)

def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS bookings;
        DROP TABLE IF EXISTS tables;
    """) 