from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "EasyWatch"
    FIREBASE_CREDENTIALS: str
    FIREBASE_WEB_API_KEY: str
    GROQ_API_KEY: str
    MODEL_NAME: str = "llama-3.3-70b-versatile"
    PROJECT_ID: str
    YOUTUBE_API_KEY: str
    UVICORN_PORT: str
    YOUTUBE_TRANSCRIPT_IO_API_TOKEN: str
    GEMINI_API_KEY: str

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()