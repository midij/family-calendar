import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database settings - simplified for local testing
    DATABASE_URL: str = "sqlite:///./family_calendar.db"  # Use SQLite for local testing
    REDIS_URL: str = "redis://localhost:6379"  # Optional for now
    
    # API settings
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "Family Calendar"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # Local development flag
    LOCAL_DEV: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings() 