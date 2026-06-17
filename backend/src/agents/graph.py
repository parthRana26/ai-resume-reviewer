import logging
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END

from src.utils.parser import parse_resume_file
from src.services.vector_store import VectorStoreService
from src.agents.parser_agent import parse_resume_content
from src.agents.analysis_agent import analyze_resume_compatibility
from src.agents.feedback_agent import generate_resume_feedback
from src.agents.report_agent import compile_final_report

logger = logging.getLogger(__name__)

# Initialize Vector Store Service
vector_store_service = VectorStoreService()

class ResumeReviewState(TypedDict):
    """
    State dictionary managed by LangGraph.
    """
    resume_id: str
    job_role: str
    file_path: str
    raw_text: Optional[str]
    parsed_content: Optional[Dict[str, Any]]
    retrieved_chunks: Optional[List[str]]
    scores: Optional[Dict[str, Any]]
    feedback: Optional[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]
    error: Optional[str]

# ----------------- Graph Nodes -----------------

def parse_resume_node(state: ResumeReviewState) -> Dict[str, Any]:
    """
    Node 1: Extract raw text from file and parse it into structured components.
    """
    file_path = state["file_path"]
    logger.info(f"LangGraph [parse_resume_node]: Extracting text from {file_path}")
    
    try:
        raw_text = parse_resume_file(file_path)
        parsed_content = parse_resume_content(raw_text)
        return {
            "raw_text": raw_text,
            "parsed_content": parsed_content
        }
    except Exception as e:
        logger.error(f"Error in parse_resume_node: {e}")
        return {"error": f"Failed to parse resume file: {e}"}

def retrieve_chunks_node(state: ResumeReviewState) -> Dict[str, Any]:
    """
    Node 2: Index raw text into ChromaDB and retrieve target role-relevant chunks.
    """
    if state.get("error"):
        return {}
        
    resume_id = state["resume_id"]
    raw_text = state["raw_text"]
    job_role = state["job_role"]
    
    logger.info(f"LangGraph [retrieve_chunks_node]: Indexing & retrieving chunks for resume {resume_id}")
    
    try:
        # Index document chunks in vector db
        vector_store_service.index_resume(resume_id, raw_text)
        
        # Retrieve context relative to job role & key skills
        chunks = vector_store_service.retrieve_relevant_chunks(resume_id, query=job_role, k=5)
        return {"retrieved_chunks": chunks}
    except Exception as e:
        logger.error(f"Error in retrieve_chunks_node: {e}")
        return {"error": f"Vector indexing or RAG retrieval failed: {e}"}

def analyze_resume_node(state: ResumeReviewState) -> Dict[str, Any]:
    """
    Node 3: Analyze the resume context using Groq LLM against the target job role.
    """
    if state.get("error"):
        return {}
        
    job_role = state["job_role"]
    retrieved_chunks = state.get("retrieved_chunks", [])
    parsed_content = state.get("parsed_content", {})
    
    logger.info(f"LangGraph [analyze_resume_node]: Analyzing resume for role: {job_role}")
    
    try:
        # Combine retrieved chunks & structured elements for richer analysis context
        context_str = f"Structured Data:\n{parsed_content}\n\nRelevant Context Chunks:\n" + "\n---\n".join(retrieved_chunks)
        scores = analyze_resume_compatibility(job_role, context_str)
        return {"scores": scores}
    except Exception as e:
        logger.error(f"Error in analyze_resume_node: {e}")
        return {"error": f"Analysis scoring failed: {e}"}

def generate_feedback_node(state: ResumeReviewState) -> Dict[str, Any]:
    """
    Node 4: Evaluate gaps, missing skills, and detailed suggestions.
    """
    if state.get("error"):
        return {}
        
    job_role = state["job_role"]
    retrieved_chunks = state.get("retrieved_chunks", [])
    parsed_content = state.get("parsed_content", {})
    
    logger.info(f"LangGraph [generate_feedback_node]: Generating feedback for role: {job_role}")
    
    try:
        context_str = f"Structured Data:\n{parsed_content}\n\nRelevant Context Chunks:\n" + "\n---\n".join(retrieved_chunks)
        feedback = generate_resume_feedback(job_role, context_str)
        return {"feedback": feedback}
    except Exception as e:
        logger.error(f"Error in generate_feedback_node: {e}")
        return {"error": f"Feedback generation failed: {e}"}

def generate_report_node(state: ResumeReviewState) -> Dict[str, Any]:
    """
    Node 5: Programmatically format and compile the final report.
    """
    if state.get("error"):
        return {}
        
    logger.info("LangGraph [generate_report_node]: Compiling final report object.")
    return compile_final_report(state)

# ----------------- Build and Compile Graph -----------------

def create_resume_reviewer_graph():
    """
    Builds the workflow graph connecting the 5 agents.
    """
    workflow = StateGraph(ResumeReviewState)
    
    # Register all nodes
    workflow.add_node("parse_resume", parse_resume_node)
    workflow.add_node("retrieve_chunks", retrieve_chunks_node)
    workflow.add_node("analyze_resume", analyze_resume_node)
    workflow.add_node("generate_feedback", generate_feedback_node)
    workflow.add_node("generate_report", generate_report_node)
    
    # Establish sequential flow
    workflow.set_entry_point("parse_resume")
    workflow.add_edge("parse_resume", "retrieve_chunks")
    workflow.add_edge("retrieve_chunks", "analyze_resume")
    workflow.add_edge("analyze_resume", "generate_feedback")
    workflow.add_edge("generate_feedback", "generate_report")
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()

# Compile the workflow graph for application imports
resume_reviewer_app = create_resume_reviewer_graph()
