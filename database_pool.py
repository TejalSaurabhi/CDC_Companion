from pymysql.cursors import DictCursor
import pymysql
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DBPool:
    def __init__(self):
        self._config = {
            "host":       os.getenv("DB_HOST",   "localhost"),
            "user":       os.getenv("DB_USER",   "root"),
            "password":   os.getenv("DB_PASSWORD",""),
            "db":         os.getenv("DB_NAME",   "cdc_companion"),
            "port":       int(os.getenv("DB_PORT",3306)),
            "autocommit": True,
            "cursorclass": DictCursor
        }
        logger.debug(f"DB Config (without password): {dict((k,v) for k,v in self._config.items() if k != 'password')}")

    def get_connection(self):
        try:
            conn = pymysql.connect(**self._config)
            logger.debug("Database connection successful")
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise

# singleton instance
db_pool = DBPool()
