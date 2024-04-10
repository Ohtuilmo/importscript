import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URI = os.getenv('DATABASE_URL')

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URI)
        return conn, conn.cursor()
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        return None, None

def close_db_connection(conn, cursor):
    if cursor:
        cursor.close()
    if conn:
        conn.close()
