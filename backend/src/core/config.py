import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Groq Configuration
    GROQ_API_KEY: str = ""
    # Model configuration – primary reasoning and fast supporting models
    PRIMARY_MODEL: str = os.getenv("PRIMARY_MODEL", "llama-3.3-70b-versatile")
    FAST_MODEL: str = os.getenv("FAST_MODEL", "llama-3.3-70b-versatile")

    # Directory Paths
    CHROMA_DB_PATH: str = "./vectorstore"
    UPLOAD_DIR: str = "./uploads"

    # Server Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    LOG_LEVEL: str = "info"

    @property
    def upload_path(self) -> Path:
        """
        Ensures the upload directory exists and returns its Path.
        """
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def chroma_path(self) -> Path:
        """
        Ensures the Chroma DB directory exists and returns its Path.
        """
        path = Path(self.CHROMA_DB_PATH)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_model(self, agent_name: str) -> str:
        """Return the appropriate model name based on the agent.

        Agents "ats", "recruiter", "hiring_manager" use the PRIMARY_MODEL.
        Agents "rewrite", "interview", "roadmap" use the FAST_MODEL.
        """
        primary_agents = {"ats", "recruiter", "hiring_manager"}
        if agent_name in primary_agents:
            return self.PRIMARY_MODEL
        return self.FAST_MODEL

settings = Settings()
# Trigger directory creation
_ = settings.upload_path
_ = settings.chroma_path
