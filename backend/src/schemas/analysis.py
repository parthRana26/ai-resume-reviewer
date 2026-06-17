from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

# Existing job role enum
class JobRoleEnum(str, Enum):
    AI_ENGINEER = "AI Engineer"
    GENAI_ENGINEER = "GenAI Engineer"
    ML_ENGINEER = "Machine Learning Engineer"
    DATA_SCIENTIST = "Data Scientist"
    SOFTWARE_ENGINEER = "Software Engineer"
    QUANT_RESEARCHER = "Quantitative Researcher"
    QUANT_DEVELOPER = "Quantitative Developer"

# Request schema
class AnalysisRequest(BaseModel):
    """Request body for initiating a resume analysis."""
    resume_id: str = Field(..., description="The ID of the uploaded resume")
    job_role: str = Field(..., description="Target job role to evaluate the resume against")

# Recommendation item (unchanged)
class RecommendationItem(BaseModel):
    """Structured feedback for a single recommendation suggestion."""
    issue: str = Field(..., description="The identified problem or area of improvement")
    why_it_matter: str = Field(..., description="Explanation of why this issue impacts the candidate's chances")
    improvement: str = Field(..., description="Actionable step to fix or enhance the resume")
    example_content: str = Field(..., description="A concrete example of how to present this on the resume")

# ---------- Shared metadata base ----------
class BaseAgentResult(BaseModel):
    """Common metadata included in every agent response."""
    model_used: str = Field(..., description="Name of the LLM model used for this agent")
    agent_name: str = Field(..., description="Identifier of the agent (e.g., ats, recruiter)")
    timestamp: str = Field(..., description="ISO‑8601 timestamp when the response was generated")
    processing_time_ms: int = Field(..., description="Time spent in the LLM call in milliseconds")
    confidence_score: Optional[float] = Field(None, description="Overall confidence of the response (0‑1) – optional for generation agents")

# ---------- Agent‑specific result models ----------
class ATSResult(BaseAgentResult):
    ats_score: int = Field(..., ge=0, le=100)
    skills_score: int = Field(..., ge=0, le=100)
    experience_score: int = Field(..., ge=0, le=100)
    project_score: int = Field(..., ge=0, le=100)
    education_score: int = Field(..., ge=0, le=100)
    overall_score: int = Field(..., ge=0, le=100)
    reasoning: str = Field(..., description="Detailed reasoning for each score")
    strengths: List[str] = Field(..., description="Identified strengths")
    weaknesses: List[str] = Field(..., description="Identified weaknesses")
    confidence: float = Field(..., ge=0.0, le=1.0)

class RecruiterResult(BaseAgentResult):
    shortlist_decision: bool = Field(...)
    recruiter_summary: str = Field(...)
    strengths: List[str] = Field(...)
    weaknesses: List[str] = Field(...)
    hiring_risk_level: str = Field(..., description="low / medium / high")

class HiringManagerResult(BaseAgentResult):
    interview_recommendation: str = Field(...)
    technical_concerns: List[str] = Field(...)
    project_quality_review: str = Field(...)
    skill_depth_assessment: str = Field(...)

class RewriteResult(BaseAgentResult):
    optimized_bullets: List[str] = Field(...)
    rewritten_projects: List[str] = Field(...)
    rewritten_experience: List[str] = Field(...)

class InterviewResult(BaseAgentResult):
    technical_questions: List[str] = Field(...)
    project_based_questions: List[str] = Field(...)
    hr_questions: List[str] = Field(...)

class RoadmapResult(BaseAgentResult):
    current_level: str = Field(...)
    next_target_role: str = Field(...)
    missing_skills: List[str] = Field(...)
    roadmap_30d: List[str] = Field(...)
    roadmap_90d: List[str] = Field(...)
    roadmap_6m: List[str] = Field(...)

# ---------- Consolidated final report ----------
class AnalysisReport(BaseModel):
    """The final structured JSON report combining evaluations and scores from all agents."""
    job_role: str = Field(...)
    # Primary evaluation (ATS) – kept for backward compatibility
    overall_score: int = Field(..., ge=0, le=100)
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    overall_explanation: str = Field(...)
    # Individual ATS related scores
    ats_score: int = Field(..., ge=0, le=100)
    ats_confidence: float = Field(..., ge=0.0, le=1.0)
    ats_explanation: str = Field(...)
    skills_score: int = Field(..., ge=0, le=100)
    skills_confidence: float = Field(..., ge=0.0, le=1.0)
    skills_explanation: str = Field(...)
    experience_score: int = Field(..., ge=0, le=100)
    experience_confidence: float = Field(..., ge=0.0, le=1.0)
    experience_explanation: str = Field(...)
    project_score: int = Field(..., ge=0, le=100)
    project_confidence: float = Field(..., ge=0.0, le=1.0)
    project_explanation: str = Field(...)
    education_score: int = Field(..., ge=0, le=100)
    education_confidence: float = Field(..., ge=0.0, le=1.0)
    education_explanation: str = Field(...)
    # Additional fields from new agents
    ats: Optional[ATSResult] = Field(default=None)
    recruiter: Optional[RecruiterResult] = Field(default=None)
    hiring_manager: Optional[HiringManagerResult] = Field(default=None)
    rewrite: Optional[RewriteResult] = Field(default=None)
    interview: Optional[InterviewResult] = Field(default=None)
    roadmap: Optional[RoadmapResult] = Field(default=None)
    # Legacy fields retained for clients that only parse old structure
    strengths: List[str] = Field(...)
    weaknesses: List[str] = Field(...)
    missing_skills: List[str] = Field(...)
    recommendations: List[RecommendationItem] = Field(...)
    final_feedback: str = Field(...)

class AnalysisStatusResponse(BaseModel):
    """API response showing status and potential final report."""
    analysis_id: str = Field(...)
    resume_id: str = Field(...)
    job_role: str = Field(...)
    status: str = Field(..., description="processing, completed, failed")
    report: Optional[AnalysisReport] = Field(None)
    error: Optional[str] = Field(None)
