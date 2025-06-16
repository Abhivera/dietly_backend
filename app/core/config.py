from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
  
    database_url: str= "postgresql://postgres:LQPnevhAbieIqCPwouEeJMkoiXJgpJEO@switchback.proxy.rlwy.net:41736/railway"
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI
    # openai_api_key: str
    # Gemini 
    gemini_api_key: str
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    
    
    # File Upload
    upload_dir: str = "uploads"
    # max_file_size: int = 10485760  # 10MB
    # allowed_extensions: List[str] = ["jpg", "jpeg", "png", "gif", "webp"]
    
    # Environment
    environment: str = "development"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Create upload directory if it doesn't exist
os.makedirs(settings.upload_dir, exist_ok=True)