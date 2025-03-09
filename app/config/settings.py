from pydantic_settings import BaseSettings
import os
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "GitHub API"
    PROJECT_VERSION: str = "0.1.0"
    GOOGLE_API_KEY: str 
    BATCH_SIZE: int = 50
    GITHUB_ACCESS_TOKEN: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    API_KEY: str = "CHRONOCODE123"
    retries: int = 3
    OPENAI_API_KEY: str
    # GitHub OAuth settings
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    
    class Config:
        env_file = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

settings = Settings()