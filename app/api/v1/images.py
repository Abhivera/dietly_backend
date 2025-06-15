# from typing import List
# from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
# from fastapi.responses import FileResponse
# from sqlalchemy.orm import Session
# from app.core.database import get_db
# from app.api.deps import get_current_user
# from app.schemas.image import ImageResponse, ImageAnalysisResponse
# from app.models.user import User
# from app.services.image_service import ImageService
# import json
# import os

# router = APIRouter()

# @router.post("/upload", response_model=ImageResponse)
# async def upload_image(
#     file: UploadFile = File(...),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     image_service = ImageService(db)
#     image = await image_service.upload_image(file, current_user)
#     return image

# @router.get("/", response_model=List[ImageResponse])
# def get_my_images(
#     skip: int = 0,
#     limit: int = 100,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     image_service = ImageService(db)
#     images = image_service.get_user_images(current_user.id, skip, limit)
#     return images

# @router.get("/{image_id}", response_model=ImageResponse)
# def get_image(
#     image_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     image_service = ImageService(db)
#     image = image_service.get_image_by_id(image_id, current_user.id)
    
#     if not image:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Image not found"
#         )
    
#     return image

# @router.get("/{image_id}/file")
# def get_image_file(
#     image_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     image_service = ImageService(db)
#     image = image_service.get_image_by_id(image_id, current_user.id)
    
#     if not image:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Image not found"
#         )
    
#     if not os.path.exists(image.file_path):
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Image file not found on disk"
#         )
    
#     return FileResponse(
#         path=image.file_path,
#         filename=image.original_filename,
#         media_type=image.content_type
#     )

# @router.get("/{image_id}/analysis", response_model=ImageAnalysisResponse)
# def get_image_analysis(
#     image_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     image_service = ImageService(db)
#     image = image_service.get_image_by_id(image_id, current_user.id)
    
#     if not image:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Image not found"
#         )
    
#     # Parse tags from JSON string
#     try:
#         tags = json.loads(image.tags) if image.tags else []
#     except json.JSONDecodeError:
#         tags = []
    
#     return ImageAnalysisResponse(
#         description=image.description or "No description available",
#         tags=tags,
#         confidence=0.8  # Default confidence
#     )

# @router.delete("/{image_id}")
# def delete_image(
#     image_id: int,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     image_service = ImageService(db)
#     success = image_service.delete_image(image_id, current_user.id)
    
#     if not success:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Image not found"
#         )
    
#     return {"message": "Image deleted successfully"}
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.image_service import ImageService
from app.api.deps import get_current_user
from typing import List
import os
import uuid
from pathlib import Path

router = APIRouter()

UPLOAD_DIR = "uploads/images"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

@router.post("/upload-and-analyze")
async def upload_and_analyze_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Upload an image and immediately analyze it for food content
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Prepare file data
        file_data = {
            'filename': unique_filename,
            'original_filename': file.filename,
            'file_path': file_path,
            'file_size': len(content),
            'content_type': file.content_type
        }
        
        # Upload and analyze
        image_service = ImageService(db)
        result = await image_service.upload_and_analyze_image(file_data, current_user.id)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{image_id}/analyze")
async def analyze_existing_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Analyze an existing image for food content
    """
    try:
        image_service = ImageService(db)
        result = await image_service.analyze_and_store_image(image_id, current_user.id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_user_images(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all user images with analysis data
    """
    try:
        image_service = ImageService(db)
        images = image_service.get_user_images_with_analysis(
            current_user.id, skip, limit
        )
        
        return {
            "images": images,
            "total": len(images),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Simple response endpoint that just returns the analysis
@router.post("/analyze-only")
async def analyze_image_only(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """
    Analyze image and return results without storing in database
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save temporary file
        temp_filename = f"temp_{uuid.uuid4()}{Path(file.filename).suffix}"
        temp_path = os.path.join(UPLOAD_DIR, temp_filename)
        
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        try:
            # Analyze the image
            from app.services.llm_service import LLMService
            llm_service = LLMService()
            analysis = await llm_service.analyze_image(temp_path)
            
            # Return the analysis directly
            return {
                "success": True,
                "analysis": {
                    "food_items": analysis.get('food_items', []),
                    "description": analysis.get('description'),
                    "calories": analysis.get('calories', 0),
                    "nutrients": analysis.get('nutrients', {}),
                    "confidence": analysis.get('confidence', 0.0)
                }
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))