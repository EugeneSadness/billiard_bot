import psycopg2
from datetime import datetime

def create_reservation(conn, client_id: int, table_id: int, start_time: datetime, end_time: datetime):
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO reservations (client_id, table_id, start_time, end_time) VALUES (%s, %s, %s, %s)",
            (client_id, table_id, start_time, end_time)
        )
        conn.commit()

def get_reservations(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM reservations")
        return cursor.fetchall()

def delete_reservation(conn, reservation_id: int):
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM reservations WHERE id = %s", (reservation_id,))
        conn.commit()
