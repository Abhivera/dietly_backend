from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
  
    database_url: str

    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440


    # Email settings
    smtp_server: str
    smtp_port: int
    smtp_username: Optional[str] 
    smtp_password: Optional[str] 
    from_email: Optional[str]

  
    # Frontend URL for password reset links
    frontend_url: str 
    
    # Rate limiting
    password_reset_rate_limit: int = 3  # per hour
    login_rate_limit: int = 5  # per minute
    
    # OpenAI
    # openai_api_key: str
    # Gemini 
    gemini_api_key: str
  
     # Add these:
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    aws_s3_bucket_name: str
    default_avatar_url: str
    
    # File Upload
    upload_dir: str = "uploads"
  
    
    # Environment
    environment: str = "development"
    
    # Google OAuth2
    google_client_id: str   
    google_client_secret: str
    google_redirect_uri: str 
    
    class Config:
        env_file = ".env"

settings = Settings()

# Create upload directory if it doesn't exist
os.makedirs(settings.upload_dir, exist_ok=True)