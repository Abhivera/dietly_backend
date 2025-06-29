from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
  
    database_url: str="postgresql+psycopg2://postgres:rbLmnGuRRJaCmYToFRPLfLsmowVInqTp@yamanote.proxy.rlwy.net:10411/railway"

    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI
    # openai_api_key: str
    # Gemini 
    gemini_api_key: str
  
    
    
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