import json
import uuid
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from src.schemas.analysis import AnalysisRequest, AnalysisStatusResponse, AnalysisReport
from src.models.database import get_resume, create_analysis, update_analysis_status, get_analysis
from src.agents.graph import resume_reviewer_app

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analysis Engine"])

async def run_langgraph_analysis(analysis_id: str, resume_id: str, file_path: str, job_role: str):
    """
    Background worker running the multi-agent LangGraph workflow.
    """
    logger.info(f"Background analysis {analysis_id} started for resume: {resume_id}")
    try:
        initial_state = {
            "resume_id": resume_id,
            "job_role": job_role,
            "file_path": file_path,
            "raw_text": None,
            "parsed_content": None,
            "retrieved_chunks": None,
            "scores": None,
            "feedback": None,
            "final_report": None,
            "error": None
        }
        
        # Invoke LangGraph asynchronously
        result = await resume_reviewer_app.ainvoke(initial_state)
        
        # Check if node executions flagged any error
        if result.get("error"):
            logger.error(f"LangGraph execution flagged an error: {result['error']}")
            update_analysis_status(
                analysis_id=analysis_id,
                status="failed",
                error_message=result["error"]
            )
        else:
            report_json = json.dumps(result.get("final_report", {}))
            update_analysis_status(
                analysis_id=analysis_id,
                status="completed",
                report_json=report_json
            )
            logger.info(f"Background analysis {analysis_id} completed successfully.")
            
    except Exception as e:
        logger.error(f"Uncaught failure in background analysis task {analysis_id}: {e}")
        update_analysis_status(
            analysis_id=analysis_id,
            status="failed",
            error_message=f"System error: {str(e)}"
        )

@router.post(
    "/analyze-resume",
    response_model=AnalysisStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger RAG and multi-agent analysis for an uploaded resume"
)
async def analyze_resume(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Triggers the resume analysis workflow. This endpoint runs asynchronously,
    spawning a background process and returning the analysis task status immediately.
    """
    resume_id = request.resume_id
    job_role = request.job_role  # Allow custom role string
    
    # Verify resume exists
    resume = get_resume(resume_id)
    if not resume:
        logger.warning(f"Analysis requested for non-existent resume ID: {resume_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID '{resume_id}' not found."
        )
        
    analysis_id = str(uuid.uuid4())
    logger.info(f"Initiating analysis {analysis_id} for resume {resume_id} and role '{job_role}'")
    
    # Store initial record in DB
    create_analysis(analysis_id, resume_id, job_role)
    
    # Dispatch processing task to background thread pool
    background_tasks.add_task(
        run_langgraph_analysis,
        analysis_id,
        resume_id,
        resume["filepath"],
        job_role
    )
    
    return AnalysisStatusResponse(
        analysis_id=analysis_id,
        resume_id=resume_id,
        job_role=job_role,
        status="processing"
    )

@router.get(
    "/analysis/{analysis_id}",
    response_model=AnalysisStatusResponse,
    summary="Get status or final compiled report of a resume analysis"
)
async def get_analysis_status(analysis_id: str):
    """
    Queries the database and retrieves the current state of an analysis task.
    If the status is 'completed', the final structured report payload is included.
    """
    logger.info(f"Retrieving analysis status for: {analysis_id}")
    analysis = get_analysis(analysis_id)
    if not analysis:
        logger.warning(f"Status check requested for invalid analysis ID: {analysis_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID '{analysis_id}' not found."
        )
        
    report = None
    if analysis["status"] == "completed" and analysis["report_json"]:
        try:
            report_dict = json.loads(analysis["report_json"])
            report = AnalysisReport(**report_dict)
        except Exception as e:
            logger.error(f"Failed to parse report_json from DB for analysis {analysis_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deserialize analysis report data."
            )
            
    return AnalysisStatusResponse(
        analysis_id=analysis["id"],
        resume_id=analysis["resume_id"],
        job_role=analysis["job_role"],
        status=analysis["status"],
        report=report,
        error=analysis["error_message"]
    )
