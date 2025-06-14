import os
import aiofiles
from fastapi import UploadFile
from app.core.config import settings

async def save_upload_file(upload_file: UploadFile, destination: str) -> None:
    """Save uploaded file to destination"""
    async with aiofiles.open(destination, 'wb') as f:
        content = await upload_file.read()
        await f.write(content)

def validate_file(file: UploadFile) -> bool:
    """Validate file type and size"""
    if not file.filename:
        return False
    
    # Check file extension
    file_extension = file.filename.split('.')[-1].lower()
    # if file_extension not in settings.allowed_extensions:
    #     return False
    
    # Check file size
    # if file.size > settings.max_file_size:
    #     return False
    
    return True

def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return filename.split('.')[-1].lower() if '.' in filename else ''