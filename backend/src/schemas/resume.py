from pydantic import BaseModel, Field

class ResumeUploadResponse(BaseModel):
    """
    Response schema after a resume is successfully uploaded.
    """
    resume_id: str = Field(..., description="Unique identifier for the uploaded resume")
    filename: str = Field(..., description="Original name of the uploaded file")
    message: str = Field(..., description="Success message")

class ResumeListItem(BaseModel):
    """
    Detailed item returned in the list of uploaded resumes.
    """
    id: str = Field(..., description="Unique identifier of the resume")
    filename: str = Field(..., description="Original name of the file")
    uploaded_at: str = Field(..., description="The upload timestamp")

