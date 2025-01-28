import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
import os

load_dotenv()

connection_pool = pooling.MySQLConnectionPool(
    pool_name="my_pool",
    pool_size=10,
    pool_reset_session=True,
    host=os.getenv("DB_HOSTNAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME")
)

def get_db_connection():
    try:
        return connection_pool.get_connection()
    except mysql.connector.errors.PoolError as e:
        raise RuntimeError("Database connection pool exhausted") from e