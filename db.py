import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "sklad"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "XDXDlol69"),
}

def get_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding('UTF8')
    return conn

def execute(sql, params=None, fetch=None):
    """
    Univerzální helper.
    fetch=None  → INSERT/UPDATE/DELETE (vrátí počet řádků)
    fetch='one' → SELECT jeden řádek
    fetch='all' → SELECT všechny řádky
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            if fetch == 'all':
                return cur.fetchall()
            if fetch == 'one':
                return cur.fetchone()
            return cur.rowcount
