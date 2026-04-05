"""
Application settings loaded from environment variables or a .env file.
All paths and tunable parameters are defined here.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables or a .env file."""

    # Paths
    domain_path: str = Field(..., env="DOMAIN_PATH")
    input_folder: str = Field("data/input", env="INPUT_FOLDER")
    output_folder: str = Field("data/output", env="OUTPUT_FOLDER")
    logs_folder: str = Field("logs", env="LOGS_FOLDER")

    # NLP
    model_name: str = Field(
        "paraphrase-multilingual-MiniLM-L12-v2", env="MODEL_NAME"
    )
    threshold: float = Field(0.75, env="THRESHOLD")
    source_column: str = Field("description", env="SOURCE_COLUMN")

    # API
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="PORT")

    class Config:
        """Configuration for Pydantic BaseSettings."""
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
