import logging
from typing import List
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from src.core.config import settings
from src.prompts.templates import ATS_SYSTEM_PROMPT
from src.utils.json_helper import parse_and_validate_json, invoke_llm_with_fallback

logger = logging.getLogger(__name__)

# Reuse existing ScoreEvaluation and AnalysisAgentOutput if needed for backward compatibility
class ScoreEvaluation(BaseModel):
    """Evaluation score with confidence index and detailed justifying explanation."""
    score: int = Field(..., ge=0, le=100, description="Score between 0 and 100")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level coefficient between 0.0 and 1.0")
    explanation: str = Field(..., description="Detailed recruiter-style explanation justifying this score")

class AnalysisAgentOutput(BaseModel):
    """Structured model for the Analysis Agent's output (legacy)."""
    overall: ScoreEvaluation = Field(..., description="Overall match evaluation")
    ats: ScoreEvaluation = Field(..., description="ATS optimization and readability evaluation")
    skills: ScoreEvaluation = Field(..., description="Technical skills fit evaluation")
    experience: ScoreEvaluation = Field(..., description="Professional work history alignment evaluation")
    education: ScoreEvaluation = Field(..., description="Education and certifications fit evaluation")
    projects: ScoreEvaluation = Field(..., description="Project relevance and technical depth evaluation")
    strengths: List[str] = Field(..., description="Key professional strengths identified on the resume")
    weaknesses: List[str] = Field(..., description="Noticeable gaps, weaknesses, or formatting flaws on the resume")

def map_to_analysis_output(data: dict) -> dict:
    """Normalize data returned by the LLM to match AnalysisAgentOutput schema."""
    scores_source = data.get("evaluation_scores", data.get("evaluation", data))
    if not isinstance(scores_source, dict):
        scores_source = data
        
    def get_score(prefix: str):
        title_prefix = prefix.title()
        keys = [
            prefix, 
            f"{prefix}_match", 
            f"{prefix}Match", 
            f"{prefix}_score",
            f"{title_prefix} Match", 
            f"{title_prefix}", 
            f"{prefix} match",
            f"{prefix} score"
        ]
        if prefix == "projects" or prefix == "project":
            keys.extend([
                "project", "projects", "project_match", "projectMatch", "project_score", 
                "Project Match", "Projects Match", "Project", "Projects", "project match"
            ])
        elif prefix == "ats":
            keys.extend([
                "ats_match", "atsMatch", "ats_score", "ATS Match", "ATS", "ats match", "ats score"
            ])
            
        obj = {}
        for k in keys:
            if k in scores_source and isinstance(scores_source[k], dict):
                obj = scores_source[k]
                break
        
        # Safely convert values to correct types
        score_val = obj.get("score", obj.get("value", 0))
        try:
            score_val = int(score_val)
        except (ValueError, TypeError):
            score_val = 0
            
        conf_val = obj.get("confidence", obj.get("confidence_level", 0.0))
        try:
            conf_val = float(conf_val)
        except (ValueError, TypeError):
            conf_val = 0.0
            
        return {
            "score": score_val,
            "confidence": conf_val,
            "explanation": str(obj.get("explanation", obj.get("reasoning", "")))
        }
    return {
        "overall": get_score("overall"),
        "ats": get_score("ats"),
        "skills": get_score("skills"),
        "experience": get_score("experience"),
        "education": get_score("education"),
        "projects": get_score("projects"),
        "strengths": data.get("strengths", []),
        "weaknesses": data.get("weaknesses", [])
    }


def analyze_resume_compatibility(job_role: str, context: str) -> dict:
    """Compatibility layer that uses the new ATS agent (primary model) but returns legacy schema.
    This preserves the existing API contract while delegating to the fresh multi‑agent implementation.
    """
    if not settings.GROQ_API_KEY:
        logger.error("GROQ_API_KEY is missing.")
        raise ValueError("GROQ_API_KEY is not configured in the environment.")
    try:
        formatted_prompt = ATS_SYSTEM_PROMPT.format(job_role=job_role, context=context)
        logger.info(f"Invoking ATS Agent (compatibility layer) for role: {job_role}")
        messages = [("system", formatted_prompt), ("user", "Please evaluate and return the JSON payload.")]
        
        # Invoke model with rate-limit fallback
        raw = invoke_llm_with_fallback(
            model_name=settings.get_model("ats"),
            messages=messages,
            temperature=0.1
        )
        parsed = parse_and_validate_json(raw, AnalysisAgentOutput, map_to_analysis_output)
        return parsed.model_dump()
    except Exception as e:
        logger.error(f"ATS compatibility layer failed: {e}")
        fallback = {"score": 0, "confidence": 0.0, "explanation": f"Error: {str(e)}"}
        return {
            "overall": fallback,
            "ats": fallback,
            "skills": fallback,
            "experience": fallback,
            "education": fallback,
            "projects": fallback,
            "strengths": ["Error during evaluation"],
            "weaknesses": ["Check logs for details"]
        }
