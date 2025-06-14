import os
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
from app.models.image import Image
from app.models.user import User
from app.schemas.image import ImageCreate
from app.core.config import settings
from app.utils.file_utils import save_upload_file, validate_file
from app.services.openai_service import OpenAIService
import json

class ImageService:
    def __init__(self, db: Session):
        self.db = db
        self.openai_service = OpenAIService()
    
    def get_user_images(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Image]:
        return self.db.query(Image).filter(Image.owner_id == user_id).offset(skip).limit(limit).all()
    
    def get_image_by_id(self, image_id: int, user_id: int) -> Optional[Image]:
        return self.db.query(Image).filter(
            Image.id == image_id, 
            Image.owner_id == user_id
        ).first()
    
    async def upload_image(self, file: UploadFile, user: User) -> Image:
        # Validate file
        if not validate_file(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type or size"
            )
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(settings.upload_dir, unique_filename)
        
        # Save file
        await save_upload_file(file, file_path)
        
        # Create database record
        image_create = ImageCreate(
            original_filename=file.filename,
            filename=unique_filename,
            file_path=file_path,
            file_size=file.size,
            content_type=file.content_type
        )
        
        db_image = Image(
            **image_create.dict(),
            owner_id=user.id
        )
        
        self.db.add(db_image)
        self.db.commit()
        self.db.refresh(db_image)
        
        # Analyze image with OpenAI (async)
        try:
            analysis = await self.openai_service.analyze_image(file_path)
            db_image.description = analysis.get("description", "")
            db_image.tags = json.dumps(analysis.get("tags", []))
            self.db.commit()
            self.db.refresh(db_image)
        except Exception as e:
            # Log error but don't fail the upload
            print(f"Image analysis failed: {e}")
        
        return db_image
    
    def delete_image(self, image_id: int, user_id: int) -> bool:
        image = self.get_image_by_id(image_id, user_id)
        if not image:
            return False
        
        # Delete file from disk
        try:
            if os.path.exists(image.file_path):
                os.remove(image.file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
        
        # Delete from database
        self.db.delete(image)
        self.db.commit()
        return True