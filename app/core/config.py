from pydantic_settings import BaseSettings
from pydantic import validator, Field
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Vietnamese Menu Analyzer"
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    HOST: str = Field(default="0.0.0.0", description="Host to bind to")
    PORT: int = Field(default=8000, ge=1, le=65535, description="Port to bind to")
    
    # Environment
    ENVIRONMENT: str = "development"
    ALLOWED_HOSTS: str = "localhost"
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000"
        ],
        description="Allowed CORS origins"
    )
    
    # Database
    DATABASE_URL: Optional[str] = None
    
    # Redis for caching
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # Service settings
    USE_MOCK_SERVICES: bool = Field(default=False, description="Use mock services for testing")
    
    # AI Model settings
    HF_API_TOKEN: Optional[str] = Field(default=None, description="Hugging Face API token")
    MODEL_ID: str = Field(default="5CD-AI/Vintern-1B-v3_5", description="Model ID for OCR")
    OCR_API_URL: str = Field(..., description="OCR API endpoint URL")
    
    # External API settings
    GOOGLE_API_KEY: Optional[str] = Field(default=None, description="Google API key")
    GOOGLE_CSE_ID: Optional[str] = Field(default=None, description="Google Custom Search Engine ID")
    
    # Cache settings
    CACHE_TTL_HOURS: int = Field(default=24, ge=1, le=168, description="Cache TTL in hours")
    
    # File upload settings
    MAX_FILE_SIZE: int = Field(default=5 * 1024 * 1024, description="Maximum file size in bytes")
    ALLOWED_EXTENSIONS: List[str] = Field(
        default_factory=lambda: [".jpg", ".jpeg", ".png", ".webp"],
        description="Allowed file extensions"
    )
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=10, ge=1, description="Rate limit per minute")
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = Field(default="logs/app.log", description="Log file path")
    
    @validator('ALLOWED_ORIGINS')
    def validate_cors_origins(cls, v):
        """Validate CORS origins and warn about wildcards"""
        if "*" in v:
            import warnings
            warnings.warn("Wildcard CORS origin detected. This should not be used in production.")
        return v
    
    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        """Validate environment name"""
        allowed_envs = ['development', 'staging', 'production', 'testing']
        if v.lower() not in allowed_envs:
            raise ValueError(f"Environment must be one of: {allowed_envs}")
        return v.lower()
    
    @validator('OCR_API_URL')
    def validate_ocr_api_url(cls, v):
        """Validate OCR API URL"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("OCR_API_URL must be a valid HTTP/HTTPS URL")
        return v.rstrip('/')
    
    @validator('LOG_FILE')
    def ensure_log_directory(cls, v):
        """Ensure log directory exists"""
        log_path = Path(v)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return str(log_path)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == 'production'
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == 'development'
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """Get the list of allowed hosts"""
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True
        
        # Environment variable mappings
        fields = {
            'SECRET_KEY': {'env': ['SECRET_KEY', 'DJANGO_SECRET_KEY']},
            'DEBUG': {'env': ['DEBUG', 'DJANGO_DEBUG']},
        }


# Singleton settings instance
settings = Settings()

# Validate critical settings on import
def validate_critical_settings():
    """Validate critical settings that must be set"""
    critical_missing = []
    
    if not settings.SECRET_KEY:
        critical_missing.append("SECRET_KEY")
    
    if not settings.OCR_API_URL:
        critical_missing.append("OCR_API_URL")
    
    if critical_missing:
        raise ValueError(f"Critical settings missing: {', '.join(critical_missing)}")

# Validate on import
try:
    validate_critical_settings()
except ValueError as e:
    if settings.ENVIRONMENT != 'testing':
        raise e