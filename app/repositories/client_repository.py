import psycopg2
from datetime import datetime


def create_client(conn, visit_date: datetime, name: str, phone: str):
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO clients (visit_date, name, phone) VALUES (%s, %s, %s)",
            (visit_date, name, phone)
        )
        conn.commit()


def get_clients(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM clients")
        return cursor.fetchall()


def delete_client(conn, client_id: int):
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM clients WHERE id = %s", (client_id,))
        conn.commit()


def update_client(conn, client_id: int, name: str, phone: str):
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE clients SET name = %s, phone = %s WHERE id = %s",
            (name, phone, client_id)
        )
        conn.commit()
