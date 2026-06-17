import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from src.core.config import settings
from src.prompts.templates import PARSER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class ExperienceItem(BaseModel):
    """
    Structured model for work experience items.
    """
    role: str = Field(..., description="Job title or role")
    company: str = Field(..., description="Company or organization name")
    duration: str = Field(..., description="Duration or dates of employment (e.g., Aug 2023 - Present)")
    description: List[str] = Field(default_factory=list, description="List of responsibilities or achievements")

class EducationItem(BaseModel):
    """
    Structured model for education credentials.
    """
    degree: str = Field(..., description="Degree or certificate name (e.g., Bachelor of Technology, Diploma)")
    institution: str = Field(..., description="Name of school, college, or university")
    duration: str = Field(..., description="Dates attended or graduation date")
    major: Optional[str] = Field(None, description="Major, concentration, or field of study")

class ProjectItem(BaseModel):
    """
    Structured model for projects completed.
    """
    name: str = Field(..., description="Project title or name")
    technologies: List[str] = Field(default_factory=list, description="Technologies or tools used")
    achievements: List[str] = Field(default_factory=list, description="Key features, bullet points, or achievements")

class ParsedResumeSchema(BaseModel):
    """
    Pydantic schema representing the structured extraction output of the resume.
    """
    skills: List[str] = Field(default_factory=list, description="Extract all technical skills, programming languages, tools, libraries, and frameworks")
    experience: List[ExperienceItem] = Field(default_factory=list, description="Extract work experience history including job titles, company names, achievements, and responsibilities")
    education: List[EducationItem] = Field(default_factory=list, description="Extract academic degrees, institutions, and majors")
    projects: List[ProjectItem] = Field(default_factory=list, description="Extract key projects, details, and technologies utilized")
    certifications: List[str] = Field(default_factory=list, description="Extract professional certifications and licenses")

from src.utils.json_helper import parse_and_validate_json, invoke_llm_with_fallback

def map_to_parser_output(data: dict) -> dict:
    """
    Normalizes keys and parses data structures returned by the LLM
    into format matching the ParsedResumeSchema properties.
    """
    skills = data.get("skills", [])
    if not isinstance(skills, list):
        skills = [str(skills)] if skills else []
        
    certifications = data.get("certifications", [])
    if not isinstance(certifications, list):
        certifications = [str(certifications)] if certifications else []

    # Parse and clean experience list
    raw_exp = data.get("experience", [])
    experience = []
    if isinstance(raw_exp, list):
        for item in raw_exp:
            if isinstance(item, dict):
                role = item.get("role", item.get("title", item.get("job_title", "Position")))
                company = item.get("company", item.get("organization", "Company"))
                duration = item.get("duration", item.get("dates", item.get("period", "N/A")))
                desc = item.get("description", item.get("achievements", item.get("bullet_points", [])))
                if isinstance(desc, str):
                    desc = [desc]
                elif not isinstance(desc, list):
                    desc = []
                experience.append({
                    "role": str(role),
                    "company": str(company),
                    "duration": str(duration),
                    "description": desc
                })
            else:
                experience.append({
                    "role": "Position",
                    "company": "Company",
                    "duration": "N/A",
                    "description": [str(item)]
                })

    # Parse and clean education list
    raw_edu = data.get("education", [])
    education = []
    if isinstance(raw_edu, list):
        for item in raw_edu:
            if isinstance(item, dict):
                degree = item.get("degree", item.get("qualification", "Degree"))
                institution = item.get("institution", item.get("school", item.get("university", "Institution")))
                duration = item.get("duration", item.get("dates", item.get("year", "N/A")))
                major = item.get("major", item.get("field_of_study", None))
                education.append({
                    "degree": str(degree),
                    "institution": str(institution),
                    "duration": str(duration),
                    "major": str(major) if major else None
                })
            else:
                education.append({
                    "degree": "Degree",
                    "institution": "Institution",
                    "duration": "N/A",
                    "major": str(item)
                })

    # Parse and clean projects list
    raw_proj = data.get("projects", [])
    projects = []
    if isinstance(raw_proj, list):
        for item in raw_proj:
            if isinstance(item, dict):
                name = item.get("name", item.get("title", item.get("project_name", "Project")))
                techs = item.get("technologies", item.get("tools", item.get("languages", [])))
                if isinstance(techs, str):
                    techs = [t.strip() for t in techs.split(",")]
                elif not isinstance(techs, list):
                    techs = []
                achievements = item.get("achievements", item.get("description", item.get("bullet_points", [])))
                if isinstance(achievements, str):
                    achievements = [achievements]
                elif not isinstance(achievements, list):
                    achievements = []
                projects.append({
                    "name": str(name),
                    "technologies": techs,
                    "achievements": achievements
                })
            else:
                projects.append({
                    "name": "Project",
                    "technologies": [],
                    "achievements": [str(item)]
                })

    return {
        "skills": skills,
        "experience": experience,
        "education": education,
        "projects": projects,
        "certifications": certifications
    }

def parse_resume_content(raw_text: str) -> dict:
    """
    Invokes Groq LLM to cleanly parse raw text into structured fields.
    Falls back to safe empty schemas on validation failure to keep analysis online.
    """
    if not settings.GROQ_API_KEY:
        logger.error("GROQ_API_KEY is missing. Cannot call parser agent.")
        raise ValueError("GROQ_API_KEY is not configured in the environment.")
        
    try:
        logger.info("Calling Groq LLM Parser Agent (Direct invoke)...")
        messages = [
            ("system", PARSER_SYSTEM_PROMPT),
            ("user", f"Here is the raw extracted resume text:\n\n{raw_text}")
        ]
        
        # Invoke model with rate-limit fallback
        raw_response_text = invoke_llm_with_fallback(
            model_name=settings.PRIMARY_MODEL,
            messages=messages,
            temperature=0.0
        )
        
        # Parse and validate with mapping helper
        parsed_data = parse_and_validate_json(
            raw_response_text,
            ParsedResumeSchema,
            map_to_parser_output
        )
        
        logger.info("Successfully parsed and validated resume text via Groq.")
        return parsed_data.model_dump()
        
    except Exception as e:
        logger.error(f"Parser agent failed, returning empty fallback layout. Error details: {e}")
        # Safe default fallback prevent pipeline crashes
        return {
            "skills": [],
            "experience": [],
            "education": [],
            "projects": [],
            "certifications": []
        }

