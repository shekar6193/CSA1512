import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "CampusPulse Cloud"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings (SQLite default, can be overridden by env variable for PostgreSQL/MySQL)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./campus_pulse.db")
    
    # CORS Origins
    CORS_ORIGINS: List[str] = ["*"]
    
    # Storage settings for image/document evidence
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE_MB: int = 10
    
    # AI Triage & Emergency Threshold
    EMERGENCY_KEYWORDS: List[str] = [
        "fire", "smoke", "gas leak", "flame", "explosion", "spark", "electric shock",
        "flooding", "water leak", "roof collapse", "elevator stuck", "chemical spill",
        "toxic", "assault", "weapon", "medical emergency", "unconscious", "blackout",
        "transformer", "structural damage", "biohazard", "trapped"
    ]
    
    # Campus SLA hours by priority
    SLA_HOURS: dict = {
        "LOW": 48,
        "MEDIUM": 24,
        "HIGH": 8,
        "CRITICAL": 2,
        "EMERGENCY": 1
    }

    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()

# Ensure uploads directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
