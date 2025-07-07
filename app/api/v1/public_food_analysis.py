from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Form
from typing import Dict, Any
import logging
from pathlib import Path
from io import BytesIO
from PIL import Image
import os
import uuid
import tempfile

from app.utils.rate_limiter import check_daily_rate_limit
from app.services.llm_service import LLMService

router = APIRouter()

# Set up logging
logger = logging.getLogger(__name__)

@router.post("/analyze-food")
async def analyze_food_image(
    file: UploadFile = File(...),
    
    request: Request = None,
    description: str = Form(None)
):
    """
    Analyze a food image and return nutritional information.
    No authentication required, but rate limited to 5 requests per day per IP.
    """
    try:
        # Check rate limit (5 requests per day per IP)
        rate_limit_info = check_daily_rate_limit(request, max_requests=5)
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail="File must be an image (JPEG, PNG, GIF, WebP)"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file size (max 10MB)
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400, 
                detail="File size too large. Maximum size is 10MB"
            )
        
        # Validate that it's actually an image
        try:
            img = Image.open(BytesIO(content))
            img.verify()
        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid image file: {str(e)}"
            )
        
        # Create temporary file for analysis
        temp_file = None
        try:
            # Create temp file with proper extension
            file_extension = Path(file.filename).suffix if file.filename else '.jpg'
            temp_file = tempfile.NamedTemporaryFile(
                suffix=file_extension, 
                delete=False
            )
            temp_file.write(content)
            temp_file.close()
            
            # Analyze the image using LLMService, passing description if provided
            llm_service = LLMService()
            analysis = await llm_service.analyze_image(temp_file.name, description=description)
            
            # Format the response
            response = {
                "success": True,
                "analysis": {
                    "is_food": analysis.get('is_food', False),
                    "food_items": analysis.get('food_items', []),
                    "description": analysis.get('description', ''),
                    "calories": analysis.get('calories', 0),
                    "nutrients": analysis.get('nutrients', {}),
                    "confidence": analysis.get('confidence', 0.0),
                    "exercise_recommendations": {
                        "steps": int(analysis.get('calories', 0) * 20),
                        "walking_km": round(analysis.get('calories', 0) / 50, 2)
                    },
                    "completed_at": datetime.now(timezone.utc).isoformat()
                },
                "rate_limit": {
                    "remaining_requests": rate_limit_info["remaining_requests"],
                    "limit": 5,
                    "period": "24 hours"
                }
            }
            
            # If it's not food, add a note
            if not analysis.get('is_food', False):
                response["analysis"]["note"] = "This image does not appear to contain food items."
            
            return response
            
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Food analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Analysis failed: {str(e)}"
        )
