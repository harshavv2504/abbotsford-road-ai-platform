from pydantic_settings import BaseSettings
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend directory
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Abbotsford API"
    DEBUG: bool = True
    
    # MongoDB
    MONGODB_URL: str
    MONGODB_DB_NAME: str = "abbotsford"
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Deepgram (for STT)
    DEEPGRAM_API_KEY: str
    
    # JWT Authentication
    JWT_SECRET: str = "your-secret-key-change-this-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours
    
    # Summarizer
    INACTIVITY_TIMEOUT_MINUTES: int = 30
    SUMMARIZER_INTERVAL_MINUTES: int = 5
    
    # CORS
    FRONTEND_URL: str = "http://localhost:3000"
    
    # HeyGen Avatar
    HEYGEN_API_KEY: str = ""
    HEYGEN_AVATAR_ID: str = "SilasHR_public"
    
    # Rate Limiting
    RATE_LIMIT_GLOBAL: str = "60/minute"
    
    class Config:
        env_file = ".env"


settings = Settings()
