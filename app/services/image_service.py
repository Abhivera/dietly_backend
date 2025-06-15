from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.image import Image
from app.services.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
    
    async def analyze_and_store_image(self, image_id: int, user_id: int) -> Dict:
        """
        Analyze an existing image and store the results
        """
        try:
            # Get the image record
            image = self.db.query(Image).filter(
                Image.id == image_id,
                Image.owner_id == user_id
            ).first()
            
            if not image:
                return {"error": "Image not found or access denied"}
            
            # Analyze the image
            analysis = await self.llm_service.analyze_image(image.file_path)
            print(f"Analysis result: {analysis}")  # Your debug print
            
            # Update the image record with analysis data
            image.is_food = analysis.get('is_food', False)
            image.analysis_description = analysis.get('description')
            image.food_items = analysis.get('food_items', [])
            image.estimated_calories = analysis.get('calories', 0)
            image.nutrients = analysis.get('nutrients', {})
            image.analysis_confidence = analysis.get('confidence', 0.0)
            image.analysis_completed = datetime.utcnow()
            
            # Commit the changes
            self.db.commit()
            self.db.refresh(image)
            
            # Return the complete response
            return {
                "success": True,
                "image_id": image.id,
                "analysis": {
                    "is_food": image.is_food,
                    "food_items": image.food_items,
                    "description": image.analysis_description,
                    "calories": image.estimated_calories,
                    "nutrients": image.nutrients,
                    "confidence": image.analysis_confidence
                }
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_and_store_image: {str(e)}")
            self.db.rollback()
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def upload_and_analyze_image(self, file_data: Dict, user_id: int) -> Dict:
        """
        Upload image and immediately analyze it
        """
        try:
            # Create image record
            image = Image(
                filename=file_data['filename'],
                original_filename=file_data['original_filename'],
                file_path=file_data['file_path'],
                file_size=file_data['file_size'],
                content_type=file_data['content_type'],
                owner_id=user_id
            )
            
            self.db.add(image)
            self.db.commit()
            self.db.refresh(image)
            
            # Analyze the uploaded image
            analysis = await self.llm_service.analyze_image(image.file_path)
            print(f"Analysis result: {analysis}")
            
            # Update with analysis data
            image.is_food = analysis.get('is_food', False)
            image.analysis_description = analysis.get('description')
            image.food_items = analysis.get('food_items', [])
            image.estimated_calories = analysis.get('calories', 0)
            image.nutrients = analysis.get('nutrients', {})
            image.analysis_confidence = analysis.get('confidence', 0.0)
            image.analysis_completed = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(image)
            
            return {
                "success": True,
                "image": image.to_dict(),
                "analysis": {
                    "is_food": analysis.get('is_food', False),
                    "food_items": analysis.get('food_items', []),
                    "description": analysis.get('description'),
                    "calories": analysis.get('calories', 0),
                    "nutrients": analysis.get('nutrients', {}),
                    "confidence": analysis.get('confidence', 0.0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in upload_and_analyze_image: {str(e)}")
            self.db.rollback()
            return {"error": f"Upload and analysis failed: {str(e)}"}
    
    def get_image_with_analysis(self, image_id: int, user_id: int) -> Optional[Dict]:
        """
        Get image with its analysis data
        """
        try:
            image = self.db.query(Image).filter(
                Image.id == image_id,
                Image.owner_id == user_id
            ).first()
            
            if not image:
                return None
            
            return {
                "id": image.id,
                "filename": image.filename,
                "original_filename": image.original_filename,
                "file_path": image.file_path,
                "content_type": image.content_type,
                "created_at": image.created_at.isoformat() if image.created_at else None,
                "analysis": {
                    "is_food": image.is_food,
                    "food_items": image.food_items or [],
                    "description": image.analysis_description,
                    "calories": image.estimated_calories,
                    "nutrients": image.nutrients or {},
                    "confidence": image.analysis_confidence,
                    "completed_at": image.analysis_completed.isoformat() if image.analysis_completed else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting image with analysis: {str(e)}")
            return None
    
    def get_user_images_with_analysis(self, user_id: int, skip: int = 0, limit: int = 20) -> List[Dict]:
        """
        Get all user images with their analysis data
        """
        try:
            images = self.db.query(Image).filter(
                Image.owner_id == user_id
            ).offset(skip).limit(limit).all()
            
            return [
                {
                    "id": img.id,
                    "filename": img.filename,
                    "original_filename": img.original_filename,
                    "created_at": img.created_at.isoformat() if img.created_at else None,
                    "analysis": {
                        "is_food": img.is_food,
                        "food_items": img.food_items or [],
                        "description": img.analysis_description,
                        "calories": img.estimated_calories,
                        "nutrients": img.nutrients or {},
                        "confidence": img.analysis_confidence,
                        "completed_at": img.analysis_completed.isoformat() if img.analysis_completed else None
                    }
                }
                for img in images
            ]
            
        except Exception as e:
            logger.error(f"Error getting user images: {str(e)}")
            return []