import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.logging import setup_logging
from src.core.database import init_db
from src.routers import health, resume, analysis

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI App
app = FastAPI(
    title="AI Resume Reviewer API",
    description="A production-grade, multi-agent RAG-powered API to parse, analyze, and score professional resumes against target roles.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event handler to bootstrap database
@app.on_event("startup")
def on_startup():
    logger.info("Initializing database schema...")
    try:
        init_db()
    except Exception as e:
        logger.critical(f"Failed to bootstrap database on startup: {e}")
        raise e

# Include Router Modules
app.include_router(health.router)
app.include_router(resume.router)
app.include_router(analysis.router)

# Serve Frontend Static Files
from fastapi.staticfiles import StaticFiles
from pathlib import Path

frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    logger.info(f"Mounting static frontend directory from: {frontend_dir}")
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
else:
    logger.warning(f"Frontend static directory not found at: {frontend_dir}")

# Centralized global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled system exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected server error occurred. Please contact the administrator.",
            "error_type": type(exc).__name__,
            "message": str(exc)
        }
    )

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting uvicorn server at http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=True
    )
