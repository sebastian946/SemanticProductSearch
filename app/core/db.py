import os
import psycopg
from psycopg.rows import dict_row
from config import settings

pgdb_name=settings.pgvector_db
pgdb_user=settings.pgvector_user
pgdb_password=settings.pgvector_password
host=settings.host
port=settings.port

def connection():
    conn = psycopg.connect(
        host=host,
        port=port,
        dbname=pgdb_name,
        user=pgdb_user,
        password=pgdb_password  )

    return conn.cursor(row_factory=dict_row)