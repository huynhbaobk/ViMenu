from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Vietnamese Menu Analyzer"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "*"  # Remove in production
    ]
    
    # Mock mode for testing
    USE_MOCK_SERVICES: bool = os.getenv("USE_MOCK_SERVICES", "false").lower() == "true"
    
    # Hugging Face settings
    HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")
    MODEL_ID: str = os.getenv("MODEL_ID", "5CD-AI/Vintern-1B-v3_5")
    OCR_API_URL: str = os.getenv("OCR_API_URL", "http://5cdaiserver.ddns.net:8000/v1")
    
    # Google Custom Search settings
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID", "")
    
    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # File upload settings
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".webp"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()