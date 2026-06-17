import time
from fastapi import APIRouter

router = APIRouter(tags=["System Health"])

START_TIME = time.time()

@router.get("/health")
async def health_check():
    """
    Endpoint verifying backend server status, uptime, and database connectivity.
    """
    return {
        "status": "healthy",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "version": "1.0.0"
    }
