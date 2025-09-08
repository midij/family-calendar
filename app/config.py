import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "sqlite:///./family_calendar.db"  # Default to SQLite for local testing
    
    # API settings
    API_V1_STR: str = "/v1"
    PROJECT_NAME: str = "Family Calendar"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # Environment settings
    ENVIRONMENT: str = "development"  # development, production
    LOCAL_DEV: bool = True
    
    # PostgreSQL settings (for production)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "family_calendar"
    POSTGRES_PORT: str = "5432"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Override DATABASE_URL if PostgreSQL environment variables are set
        # Only use PostgreSQL if explicitly requested via USE_POSTGRES env var
        if os.getenv("USE_POSTGRES"):
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            self.LOCAL_DEV = False
    
    class Config:
        env_file = ".env"

settings = Settings() 