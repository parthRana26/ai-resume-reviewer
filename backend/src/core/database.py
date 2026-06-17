import sqlite3
import os
import logging
from contextlib import contextmanager
from src.core.config import settings

logger = logging.getLogger(__name__)

# Locate metadata DB inside vectorstore directory to centralize data storage
DB_PATH = os.path.join(settings.CHROMA_DB_PATH, "metadata.db")

@contextmanager
def get_db_connection():
    """
    Context manager that yields a thread-safe connection to the SQLite database.
    Automatically commits transactions or rolls back on error.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error occurred: {e}")
        raise e
    finally:
        conn.close()

def init_db() -> None:
    """
    Creates tables in SQLite if they don't already exist.
    """
    # Ensure database folder exists
    settings.chroma_path
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Resumes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Analyses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                resume_id TEXT NOT NULL,
                job_role TEXT NOT NULL,
                status TEXT NOT NULL,
                report_json TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
            )
        """)
        
        logger.info("Database metadata tables initialized successfully.")
