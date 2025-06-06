
import os
import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
import magic

class FileUploadHelper:
    ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_image(file: UploadFile) -> bool:
        """Validate uploaded image file"""
        # Check file size
        if file.size and file.size > FileUploadHelper.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Read file content to check MIME type
        file_content = file.file.read()
        file.file.seek(0)  # Reset file pointer
        
        # Check MIME type using python-magic
        mime_type = magic.from_buffer(file_content, mime=True)
        if mime_type not in FileUploadHelper.ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        return True
    
    @staticmethod
    def save_image(file: UploadFile, upload_dir: str = "uploads") -> str:
        """Save uploaded image and return file path"""
        FileUploadHelper.validate_image(file)
        
        # Create upload directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split(".")[-1] if file.filename else "jpg"
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)
        
        return file_path
    
    @staticmethod
    def resize_image(file_path: str, max_width: int = 800, max_height: int = 600) -> str:
        """Resize image to specified dimensions"""
        try:
            with Image.open(file_path) as img:
                # Calculate new dimensions while maintaining aspect ratio
                ratio = min(max_width / img.width, max_height / img.height)
                if ratio < 1:
                    new_width = int(img.width * ratio)
                    new_height = int(img.height * ratio)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Save resized image
                img.save(file_path, optimize=True, quality=85)
            
            return file_path
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

class ResponseHelper:
    @staticmethod
    def success_response(data=None, message: str = "Success"):
        return {"status": "success", "message": message, "data": data}
    
    @staticmethod
    def error_response(message: str, details=None):
        response = {"status": "error", "message": message}
        if details:
            response["details"] = details
        return response

class ValidationHelper:
    @staticmethod
    def validate_uuid(uuid_string: str) -> bool:
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_positive_integer(value: int) -> bool:
        return isinstance(value, int) and value > 0
    
    @staticmethod
    def validate_email_format(email: str) -> bool:
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None