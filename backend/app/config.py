import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Supervity Exception Resolution Workbench"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = "supervity-assessment-prototype-secret-key-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours for demo purposes
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:supervity_secure_password_2026@localhost:5432/supervity_workbench"
    
    # AI Integration
    # Supported: "mock", "gemini", "openai"
    AI_PROVIDER: str = "mock"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    # Default Policy Rules (stored in DB initially and dynamically loaded)
    AUTO_RESOLVE_CONFIDENCE_MIN: float = 0.90
    HUMAN_REVIEW_CONFIDENCE_MIN: float = 0.70
    HIGH_RISK_AMOUNT_THRESHOLD: float = 50000.00  # Transactions above 50k are high risk
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
