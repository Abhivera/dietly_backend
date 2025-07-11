from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.image_service import ImageService
from app.api.deps import get_current_user, get_current_superuser
from typing import List
import os
import uuid
import time
import asyncio
from pathlib import Path
from io import BytesIO
from PIL import Image
from pydantic import BaseModel
from app.models.image import Image
import logging
from PIL import Image as PILImage

router = APIRouter()

UPLOAD_DIR = "uploads/images"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

class IsMealUpdateRequest(BaseModel):
    is_meal: bool

@router.post("/upload-and-analyze")
async def upload_and_analyze_image(
    file: UploadFile = File(...),
    description: str = Form(None),  # Optional text field
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Upload an image and immediately analyze it for food content
    This now uses the fixed ImageService method that analyzes from memory
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate that it's actually an image
        try:
            img = PILImage.open(BytesIO(content))
            img.verify()
        except Exception as e:
            logging.error(f"Image validation failed: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid image file: {e}")
        
        # Create a BytesIO object from the content for the service
        file_obj = BytesIO(content)
        
        # Extract required parameters
        original_filename = file.filename
        content_type = file.content_type
        
        # Call ImageService with the correct parameters
        image_service = ImageService(db)
        result = await image_service.upload_and_analyze_image(
            file_obj=file_obj,
            original_filename=original_filename,
            file_size=file_size,
            content_type=content_type,
            user_id=current_user.id,
            user_description=description  # Pass the optional description
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Include the user-provided description in the response if present
        if description:
            result["user_description"] = description
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/{image_id}")
async def get_image_with_analysis(
    image_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get image details including analysis data
    """
    try:
        image_service = ImageService(db)
        result = image_service.get_image_with_analysis(image_id, current_user.id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve image: {str(e)}")

@router.get("/{image_id}/fresh-url")
async def get_image_with_fresh_url(
    image_id: int,
    expiration: int = 3600,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get image details with a fresh presigned URL
    """
    try:
        image_service = ImageService(db)
        result = image_service.get_image_with_presigned_url(image_id, current_user.id, expiration)
        
        if not result:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve image: {str(e)}")

@router.get("/")


async def get_user_images(
    skip: int = 0,
    limit: int = 20,
    date: str = None,  # format: YYYY-MM-DD
    week: str = None,  # format: YYYY-Www
    month: str = None, # format: YYYY-MM
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all user images with analysis data.
    Optional filters:
      - date: YYYY-MM-DD (highest priority)
      - week: YYYY-Www (ISO week, e.g., 2024-W23)
      - month: YYYY-MM (e.g., 2024-06)
    Only one filter is applied at a time, with priority: date > week > month.
    """
    try:
        filter_type = None
        filter_value = None
        if date:
            filter_type = 'date'
            filter_value = date
        elif week:
            filter_type = 'week'
            filter_value = week
        elif month:
            filter_type = 'month'
            filter_value = month
        image_service = ImageService(db)
        images = image_service.get_user_images_with_analysis(
            current_user.id, skip, limit, filter_type, filter_value
        )
        return {
            "images": images,
            "total": len(images),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve images: {str(e)}")

@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Hard delete an image (remove from database)
    """
    try:
        image_service = ImageService(db)
        result = image_service.delete_image(image_id, current_user.id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

# Testing endpoints
@router.post("/{image_id}/test")
async def test_image_processing(
    image_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Test endpoint to check S3 access and analysis capabilities
    """
    try:
        image_service = ImageService(db)
        result = await image_service.test_s3_and_analysis(image_id, current_user.id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@router.post("/test-llm")
async def test_llm_service(current_user = Depends(get_current_user)):
    """
    Test LLM service connection
    """
    try:
        from app.services.llm_service import LLMService
        llm_service = LLMService()
        result = await llm_service.test_api_connection()
        
        return {
            "success": result,
            "message": "LLM service is working" if result else "LLM service test failed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM test failed: {str(e)}")

@router.get("/all-by-user/{user_id}")
async def get_all_images_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_superuser)
):
    """
    Superuser-only: Get all images for a specific user_id
    """
    try:
        image_service = ImageService(db)
        images = image_service.get_user_images_with_analysis(user_id, skip=0, limit=10000)
        if not images:
            raise HTTPException(status_code=404, detail="No images found for this user")
        return {"images": images, "user_id": user_id, "total": len(images)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve images: {str(e)}")

@router.patch("/is-meal/{image_id}")
async def update_is_meal(
    image_id: int,
    req: IsMealUpdateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update the is_meal field for an image, only if is_food is true.
    """
    try:
        image = db.query(Image).filter(
            Image.id == image_id,
            Image.owner_id == current_user.id
        ).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        if not image.is_food:
            raise HTTPException(status_code=400, detail="Cannot set is_meal: image is not food")
        image.is_meal = req.is_meal
        db.commit()
        db.refresh(image)
        return {"success": True, "image_id": image.id, "is_meal": image.is_meal}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update is_meal: {str(e)}")