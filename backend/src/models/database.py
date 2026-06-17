import logging
from typing import Optional, Dict, Any
from src.core.database import get_db_connection

logger = logging.getLogger(__name__)

def create_resume(resume_id: str, filename: str, filepath: str) -> None:
    """
    Inserts a new uploaded resume record into the DB.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO resumes (id, filename, filepath) VALUES (?, ?, ?)",
            (resume_id, filename, filepath)
        )
        logger.info(f"Created resume record: {resume_id}")

def get_resume(resume_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a resume record by its ID.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def create_analysis(analysis_id: str, resume_id: str, job_role: str) -> None:
    """
    Creates a new analysis record with "processing" status.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO analyses (id, resume_id, job_role, status) VALUES (?, ?, ?, ?)",
            (analysis_id, resume_id, job_role, "processing")
        )
        logger.info(f"Created analysis record: {analysis_id} for resume {resume_id}")

def update_analysis_status(
    analysis_id: str, 
    status: str, 
    report_json: Optional[str] = None, 
    error_message: Optional[str] = None
) -> None:
    """
    Updates status, report_json, or error_message of an analysis record.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE analyses SET status = ?, report_json = ?, error_message = ? WHERE id = ?",
            (status, report_json, error_message, analysis_id)
        )
        logger.info(f"Updated analysis {analysis_id} to status: {status}")

def get_analysis(analysis_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves analysis progress or results by ID.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT a.id, a.resume_id, a.job_role, a.status, a.report_json, a.error_message, a.created_at, r.filename
            FROM analyses a
            JOIN resumes r ON a.resume_id = r.id
            WHERE a.id = ?
            """,
            (analysis_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

def list_resumes() -> list:
    """
    Retrieves all uploaded resume records ordered by upload date descending.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, uploaded_at FROM resumes ORDER BY uploaded_at DESC")
        return [dict(row) for row in cursor.fetchall()]

