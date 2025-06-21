import os
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create a SimpleConnectionPool once at startup
db_pool: pool.SimpleConnectionPool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL
)

@contextmanager
def get_db_cursor():
    """
    Context manager that yields (conn, cursor) from the Postgres pool
    using a RealDictCursor so cursor.fetchone() returns dicts.
    """
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield conn, cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        db_pool.putconn(conn)

def init_db():
    """Create tables if they do not exist in the connected Postgres database."""
    with get_db_cursor() as (_, cur):
        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_data (
            id SERIAL PRIMARY KEY,
            name VARCHAR(500) NOT NULL,
            roll_no VARCHAR(10) NOT NULL,
            email_id VARCHAR(500),
            drive_link VARCHAR(500),
            status_num INT DEFAULT 0,
            profiles VARCHAR(500),
            assigned_to VARCHAR(30),
            submission_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reviewer_data (
            id SERIAL PRIMARY KEY,
            name VARCHAR(500) NOT NULL UNIQUE,
            password VARCHAR(30) NOT NULL,
            reviewsnumber INT NOT NULL,
            cvsreviewed INT NOT NULL DEFAULT 0,
            linkedin VARCHAR(500),
            email VARCHAR(500),
            rprofilez VARCHAR(500)
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews_data (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            roll_no VARCHAR(10),
            email_id VARCHAR(255),
            reviewer_name VARCHAR(255),
            reviewer_linkedin VARCHAR(500),
            reviewer_email VARCHAR(500),
            drive_link VARCHAR(255),
            review TEXT,
            submission_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        """)

# Initialize on import
init_db()
