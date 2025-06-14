from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.schemas.image import ImageResponse, ImageAnalysisResponse
from app.models.user import User
from app.services.image_service import ImageService
import json
import os

router = APIRouter()

@router.post("/upload", response_model=ImageResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image_service = ImageService(db)
    image = await image_service.upload_image(file, current_user)
    return image

@router.get("/", response_model=List[ImageResponse])
def get_my_images(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image_service = ImageService(db)
    images = image_service.get_user_images(current_user.id, skip, limit)
    return images

@router.get("/{image_id}", response_model=ImageResponse)
def get_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image_service = ImageService(db)
    image = image_service.get_image_by_id(image_id, current_user.id)
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    return image

@router.get("/{image_id}/file")
def get_image_file(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image_service = ImageService(db)
    image = image_service.get_image_by_id(image_id, current_user.id)
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    if not os.path.exists(image.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image file not found on disk"
        )
    
    return FileResponse(
        path=image.file_path,
        filename=image.original_filename,
        media_type=image.content_type
    )

@router.get("/{image_id}/analysis", response_model=ImageAnalysisResponse)
def get_image_analysis(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image_service = ImageService(db)
    image = image_service.get_image_by_id(image_id, current_user.id)
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Parse tags from JSON string
    try:
        tags = json.loads(image.tags) if image.tags else []
    except json.JSONDecodeError:
        tags = []
    
    return ImageAnalysisResponse(
        description=image.description or "No description available",
        tags=tags,
        confidence=0.8  # Default confidence
    )

@router.delete("/{image_id}")
def delete_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    image_service = ImageService(db)
    success = image_service.delete_image(image_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    return {"message": "Image deleted successfully"}