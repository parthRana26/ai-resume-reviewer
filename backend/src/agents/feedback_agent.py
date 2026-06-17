import logging
from typing import List
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from src.core.config import settings
from src.prompts.templates import FEEDBACK_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class RecommendationItemSchema(BaseModel):
    """
    Detailed Pydantic model for a single structured recommendation.
    """
    issue: str = Field(..., description="The specific issue or gap identified on the resume")
    why_it_matters: str = Field(..., description="The impact this issue has on ATS or a recruiter's evaluation")
    improvement: str = Field(..., description="Clear, step-by-step instructions on how to rectify the issue")
    example_content: str = Field(..., description="A concrete, high-quality copy-pasteable example of how this should look")

class FeedbackAgentOutput(BaseModel):
    """
    Structured response layout for the Feedback Agent.
    """
    missing_skills: List[str] = Field(..., description="List of important skills/tools expected for the job role but missing from the resume")
    recommendations: List[RecommendationItemSchema] = Field(..., description="List of granular recommendations")
    final_feedback: str = Field(..., description="A final encouraging, professional executive summary paragraph outlining main action items")

from src.utils.json_helper import parse_and_validate_json, invoke_llm_with_fallback

def map_to_feedback_output(data: dict) -> dict:
    """
    Normalizes keys and parses data structures returned by the LLM
    into format matching the FeedbackAgentOutput schema.
    """
    missing_skills = data.get("missing_skills", data.get("missingSkills", []))
    if not isinstance(missing_skills, list):
        missing_skills = [str(missing_skills)] if missing_skills else []
        
    raw_recs = data.get("recommendations", [])
    recommendations = []
    if isinstance(raw_recs, list):
        for item in raw_recs:
            if isinstance(item, dict):
                issue = item.get("issue", item.get("problem", "Improvement Area"))
                why = item.get("why_it_matter", item.get("why", "Impacts ATS readability"))
                imp = item.get("improvement", item.get("solution", "Refine phrasing"))
                ex = item.get("example_content", item.get("example", ""))
                recommendations.append({
                    "issue": str(issue),
                    "why_it_matter": str(why),
                    "improvement": str(imp),
                    "example_content": str(ex)
                })
            else:
                recommendations.append({
                    "issue": "Improvement Area",
                    "why_it_matter": "Impacts ATS readability",
                    "improvement": str(item),
                    "example_content": ""
                })
                
    final_feedback = data.get("final_feedback", data.get("finalFeedback", ""))
    
    return {
        "missing_skills": missing_skills,
        "recommendations": recommendations,
        "final_feedback": str(final_feedback)
    }

def generate_resume_feedback(job_role: str, context: str) -> dict:
    """
    Uses Groq LLM to produce structured recommendations and actionable feedback for the resume.
    Falls back to safe default feedback if evaluation fails to keep the pipeline alive.
    """
    if not settings.GROQ_API_KEY:
        logger.error("GROQ_API_KEY is missing.")
        raise ValueError("GROQ_API_KEY is not configured in the environment.")
        
    try:
        formatted_prompt = FEEDBACK_SYSTEM_PROMPT.format(job_role=job_role, context=context)
        logger.info(f"Invoking Groq Feedback Agent (Direct invoke) for role: {job_role}")
        
        messages = [
            ("system", formatted_prompt),
            ("user", "Examine the resume details and context to construct structured recommendations.")
        ]
        
        # Invoke model with rate-limit fallback
        raw_response_text = invoke_llm_with_fallback(
            model_name=settings.FAST_MODEL,
            messages=messages,
            temperature=0.2
        )
        
        # Parse and validate with mapping helper
        parsed_data = parse_and_validate_json(
            raw_response_text,
            FeedbackAgentOutput,
            map_to_feedback_output
        )
        
        logger.info("Successfully generated feedback via Groq.")
        return parsed_data.model_dump()
        
    except Exception as e:
        logger.error(f"Feedback agent failed, returning fallback recommendations. Error details: {e}")
        # Safe default fallback prevent pipeline crashes
        return {
            "missing_skills": [],
            "recommendations": [
                {
                    "issue": "Review technical keywords density",
                    "why_it_matter": "Increases matching score in ATS search engines",
                    "improvement": "Add specific technologies matching standard role profiles",
                    "example_content": "Add a dedicated Skills Matrix section listing core packages/tools."
                }
            ],
            "final_feedback": "Resume evaluation completed. Review the individual scoring metrics to identify optimization targets."
        }

