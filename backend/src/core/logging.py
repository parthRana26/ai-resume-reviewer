import logging
import sys
from src.core.config import settings

def setup_logging() -> None:
    """
    Sets up application-wide logging format and level.
    """
    log_level = settings.LOG_LEVEL.upper()
    
    # Configure the root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )
    
    # Optional: Suppress noisy third-party libraries
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("hnswlib").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at level: {log_level}")
