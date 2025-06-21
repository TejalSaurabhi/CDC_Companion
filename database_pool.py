import os
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg2
from psycopg2 import pool, OperationalError
from psycopg2.extras import RealDictCursor
import time

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
    Includes connection validation and retry logic.
    """
    conn = None
    cursor = None
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = db_pool.getconn()
            
            # Test the connection with a simple query
            test_cursor = conn.cursor()
            test_cursor.execute("SELECT 1")
            test_cursor.close()
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            yield conn, cursor
            conn.commit()
            break
            
        except (OperationalError, psycopg2.InterfaceError) as e:
            retry_count += 1
            if conn:
                try:
                    db_pool.putconn(conn, close=True)  # Close bad connection
                except:
                    pass
                conn = None
            
            if retry_count >= max_retries:
                raise e
            
            # Wait before retry
            time.sleep(0.1 * retry_count)
            continue
            
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise e
            
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if conn:
                try:
                    db_pool.putconn(conn)
                except:
                    pass

def init_db():
    """Create tables if they do not exist in the connected Postgres database."""
    with get_db_cursor() as (_, cur):
        # Create user_data table
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
        
        # Create reviewer_data table
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
        
        # Create reviews_data table with structured review columns
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
            structure_format TEXT,
            domain_relevance TEXT,
            depth_explanation TEXT,
            language_grammar TEXT,
            project_improvements TEXT,
            additional_suggestions TEXT,
            submission_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        """)

# Initialize on import
try:
    init_db()
except Exception as e:
    print(f"Database initialization failed: {e}")
    # Don't crash the app, let it handle the error gracefully
