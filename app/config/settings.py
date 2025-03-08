from pydantic_settings import BaseSettings
import os
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "GitHub API"
    PROJECT_VERSION: str = "0.1.0"
    GOOGLE_API_KEY: str 
    BATCH_SIZE: int = 50
    GITHUB_ACCESS_TOKEN: str

    class Config:
        env_file = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / ".env"
        env_file_encoding = "utf-8"

settings = Settings()