import os
import uuid
import logging
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from src.core.config import settings
from src.schemas.resume import ResumeUploadResponse, ResumeListItem
from src.models.database import create_resume, list_resumes

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Resume Management"])

# Set of allowed extensions for upload validation
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

@router.post(
    "/upload-resume",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a resume (PDF or DOCX)"
)
async def upload_resume(file: UploadFile = File(...)):
    """
    Accepts a PDF or DOCX file, writes it locally to the server upload directory,
    and returns a unique resume ID to reference in subsequent analysis calls.
    """
    filename = file.filename
    _, ext = os.path.splitext(filename.lower())
    
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"File upload rejected due to invalid extension: {filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Only PDF and DOCX are allowed."
        )
        
    resume_id = str(uuid.uuid4())
    logger.info(f"Uploading file '{filename}' assigning resume ID: {resume_id}")
    
    # Define local storage file name to prevent collision
    safe_filename = f"{resume_id}{ext}"
    dest_path = settings.upload_path / safe_filename
    
    try:
        # Save file chunks to disk
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        logger.info(f"File successfully written to path: {dest_path}")
        
        # Insert record to metadata DB
        create_resume(resume_id, filename, str(dest_path))
        
        return ResumeUploadResponse(
            resume_id=resume_id,
            filename=filename,
            message="Resume uploaded and registered successfully."
        )
    except Exception as e:
        logger.error(f"Failed to process uploaded file: {e}")
        # Clean up file if created partially
        if dest_path.exists():
            os.remove(dest_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred writing the file: {str(e)}"
        )

@router.get(
    "/resumes",
    response_model=List[ResumeListItem],
    summary="List all uploaded resumes"
)
async def get_resumes():
    """
    Retrieves a list of all resumes uploaded and registered in the system database.
    """
    try:
        return list_resumes()
    except Exception as e:
        logger.error(f"Failed to list resumes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resumes from database."
        )

