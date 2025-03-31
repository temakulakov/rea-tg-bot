import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )

    @contextmanager
    def get_cursor(self):
        conn = self.connection_pool.getconn()
        try:
            yield conn.cursor()
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.connection_pool.putconn(conn)

db = Database()