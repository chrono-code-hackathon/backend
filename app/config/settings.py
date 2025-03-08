from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "GitHub API"
    PROJECT_VERSION: str = "0.1.0"

settings = Settings()