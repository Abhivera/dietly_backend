from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.image import Image
from app.services.llm_service import LLMService
from app.services.s3_service import S3Service
import logging
import requests
from io import BytesIO
import asyncio
import re

logger = logging.getLogger(__name__)


class ImageService:
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()
        self.s3_service = S3Service()

    async def upload_and_analyze_image(self, file_obj, user_id: int, original_filename: str, file_size: int, content_type: str, user_description: str = None) -> Dict:
        """Upload image to S3 and analyze it using content from memory. Optionally use user description."""
        try:
            # Reset file pointer to beginning
            file_obj.seek(0)
            
            # Read content for analysis before upload
            image_content = file_obj.read()
            
            # Reset file pointer for S3 upload
            file_obj.seek(0)
            
            # Upload to S3
            upload_result = self.s3_service.upload_file(file_obj, user_id, original_filename)

            if not upload_result['success']:
                return {"error": upload_result['error']}

            # Create image record in database
            image = Image(
                filename=upload_result['filename'],
                original_filename=upload_result['original_filename'],
                file_url=upload_result['file_url'],
                s3_key=upload_result['s3_key'],
                s3_bucket=upload_result['bucket'],
                file_size=file_size,
                content_type=content_type,
                owner_id=user_id
            )

            self.db.add(image)
            self.db.commit()
            self.db.refresh(image)

            # Analyze using image content from memory instead of S3 URL
            analysis = await self.llm_service.analyze_image_content(image_content, content_type)
            print(f"Analysis result: {analysis}")

            # If user_description is provided, append or use it in the analysis description
            if user_description:
                if analysis.get('description'):
                    analysis['description'] = f"{analysis['description']} (User note: {user_description})"
                else:
                    analysis['description'] = f"User note: {user_description}"

            # Calculate exercise recommendations dynamically
            calories = analysis.get('calories', 0)
            exercise_recommendations = analysis.get(
                'exercise_recommendations',
                {"steps": int(calories * 20), "walking_km": round(calories / 50, 2)}
            )

            # Update image with analysis results
            image.is_food = analysis.get('is_food', False)
            image.is_meal = True if image.is_food else False  # Set is_meal True if is_food is True
            image.analysis_description = analysis.get('description')
            image.food_items = analysis.get('food_items', [])
            image.estimated_calories = calories
            image.nutrients = analysis.get('nutrients', {})
            image.analysis_confidence = analysis.get('confidence', 0.0)
            image.analysis_completed = datetime.now(timezone.utc)
            image.description = analysis.get('description')  # Set top-level description

            self.db.commit()
            self.db.refresh(image)

            # Patch the image dict's analysis to match the top-level one
            image_dict = image.to_dict()
            if 'analysis' in image_dict:
                image_dict['analysis']['exercise_recommendations'] = exercise_recommendations

            return {
                "success": True,
                "image": image_dict
            }

        except Exception as e:
            logger.error(f"Error in upload_and_analyze_image: {str(e)}")
            self.db.rollback()
            return {"error": f"Upload and analysis failed: {str(e)}"}

    async def upload_image_only(self, file_obj, original_filename: str, file_size: int, content_type: str, user_id: int) -> Dict:
        """Upload image to S3 without analysis"""
        try:
            file_obj.seek(0)
            upload_result = self.s3_service.upload_file(file_obj, user_id, original_filename)

            if not upload_result['success']:
                return {"error": upload_result['error']}

            image = Image(
                filename=upload_result['filename'],
                original_filename=upload_result['original_filename'],
                file_url=upload_result['file_url'],
                s3_key=upload_result['s3_key'],
                s3_bucket=upload_result['bucket'],
                file_size=file_size,
                content_type=content_type,
                owner_id=user_id
            )

            self.db.add(image)
            self.db.commit()
            self.db.refresh(image)

            return {
                "success": True,
                "image": image.to_dict()
            }

        except Exception as e:
            logger.error(f"Error in upload_image_only: {str(e)}")
            self.db.rollback()
            return {"error": f"Upload failed: {str(e)}"}

    async def upload_image_with_analysis(self, file_obj, original_filename: str, file_size: int, content_type: str, user_id: int, analysis: Dict) -> Dict:
        """Upload image to S3 with pre-computed analysis"""
        try:
            file_obj.seek(0)
            upload_result = self.s3_service.upload_file(file_obj, user_id, original_filename)

            if not upload_result['success']:
                return {"error": upload_result['error']}

            image = Image(
                filename=upload_result['filename'],
                original_filename=upload_result['original_filename'],
                file_url=upload_result['file_url'],
                s3_key=upload_result['s3_key'],
                s3_bucket=upload_result['bucket'],
                file_size=file_size,
                content_type=content_type,
                owner_id=user_id,
                # Set analysis data immediately
                is_food=analysis.get('is_food', False),
                analysis_description=analysis.get('description'),
                food_items=analysis.get('food_items', []),
                estimated_calories=analysis.get('calories', 0),
                nutrients=analysis.get('nutrients', {}),
                analysis_confidence=analysis.get('confidence', 0.0),
                analysis_completed=datetime.now(timezone.utc)
            )

            self.db.add(image)
            self.db.commit()
            self.db.refresh(image)

            return {
                "success": True,
                "image": image.to_dict()
            }

        except Exception as e:
            logger.error(f"Error in upload_image_with_analysis: {str(e)}")
            self.db.rollback()
            return {"error": f"Upload failed: {str(e)}"}

    async def update_image_analysis(self, image_id: int, analysis: Dict) -> Dict:
        """Update existing image with analysis results"""
        try:
            image = self.db.query(Image).filter(Image.id == image_id).first()
            
            if not image:
                return {"error": "Image not found"}

            image.is_food = analysis.get('is_food', False)
            image.analysis_description = analysis.get('description')
            image.food_items = analysis.get('food_items', [])
            image.estimated_calories = analysis.get('calories', 0)
            image.nutrients = analysis.get('nutrients', {})
            image.analysis_confidence = analysis.get('confidence', 0.0)
            image.analysis_completed = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(image)

            return {
                "success": True,
                "image": image.to_dict()
            }

        except Exception as e:
            logger.error(f"Error in update_image_analysis: {str(e)}")
            self.db.rollback()
            return {"error": f"Update failed: {str(e)}"}

    async def analyze_existing_image(self, image_id: int, user_id: int) -> Dict:
        """Analyze an existing image using S3 content"""
        try:
            image = self.db.query(Image).filter(
                Image.id == image_id,
                Image.owner_id == user_id
            ).first()

            if not image:
                return {"error": "Image not found or access denied"}

            # Try to get image content from S3
            try:
                image_content = self.s3_service.get_file_content(image.s3_key)
                if image_content:
                    # Analyze using content from S3
                    analysis = await self.llm_service.analyze_image_content(image_content, image.content_type)
                else:
                    # Fallback: try to download from URL
                    analysis = await self._analyze_from_url_fallback(image.file_url)
            except Exception as e:
                logger.warning(f"Failed to get S3 content, trying URL fallback: {str(e)}")
                analysis = await self._analyze_from_url_fallback(image.file_url)

            # Update image with analysis
            image.is_food = analysis.get('is_food', False)
            image.analysis_description = analysis.get('description')
            image.food_items = analysis.get('food_items', [])
            image.estimated_calories = analysis.get('calories', 0)
            image.nutrients = analysis.get('nutrients', {})
            image.analysis_confidence = analysis.get('confidence', 0.0)
            image.analysis_completed = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(image)

            return {
                "success": True,
                "image_id": image.id,
                "analysis": {
                    "is_food": image.is_food,
                    "food_items": image.food_items,
                    "description": image.analysis_description,
                    "calories": image.estimated_calories,
                    "nutrients": image.nutrients,
                    "confidence": image.analysis_confidence,
                    "completed_at": image.analysis_completed.isoformat() if image.analysis_completed else None
                }
            }

        except Exception as e:
            logger.error(f"Error in analyze_existing_image: {str(e)}")
            self.db.rollback()
            return {"error": f"Analysis failed: {str(e)}"}

    async def _analyze_from_url_fallback(self, url: str) -> Dict:
        """Fallback method to analyze image by downloading from URL"""
        try:
            # Download image content from URL
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            image_content = response.content
            content_type = response.headers.get('Content-Type', 'image/jpeg')
            
            # Analyze using downloaded content
            analysis = await self.llm_service.analyze_image_content(image_content, content_type)
            return analysis
            
        except Exception as e:
            logger.error(f"URL fallback analysis failed: {str(e)}")
            return {
                "description": f"Error analyzing image: {str(e)}",
                "is_food": False,
                "food_items": [],
                "calories": 0,
                "nutrients": {"protein": 0, "carbs": 0, "fat": 0, "sugar": 0},
                "confidence": 0.0
            }

    async def analyze_and_store_image(self, image_id: int, user_id: int) -> Dict:
        """Re-analyze an existing image (alias for analyze_existing_image)"""
        return await self.analyze_existing_image(image_id, user_id)

    def delete_image(self, image_id: int, user_id: int) -> Dict:
        """Delete image and remove from S3"""
        try:
            image = self.db.query(Image).filter(
                Image.id == image_id,
                Image.owner_id == user_id
            ).first()

            if not image:
                return {"error": "Image not found or access denied"}

            s3_deleted = self.s3_service.delete_file(image.s3_key)
            if not s3_deleted:
                logger.warning(f"Failed to delete S3 object: {image.s3_key}")

            self.db.delete(image)
            self.db.commit()

            return {"success": True, "message": "Image deleted successfully"}

        except Exception as e:
            logger.error(f"Error deleting image: {str(e)}")
            self.db.rollback()
            return {"error": f"Delete failed: {str(e)}"}

    def get_image_with_analysis(self, image_id: int, user_id: int) -> Optional[Dict]:
        """Get image with its analysis data"""
        try:
            image = self.db.query(Image).filter(
                Image.id == image_id,
                Image.owner_id == user_id
            ).first()
            if not image:
                return None
            image_dict = image.to_dict()
            if 'analysis' in image_dict:
                if 'exercise_recommendations' not in image_dict['analysis'] or not image_dict['analysis']['exercise_recommendations']:
                    image_dict['analysis']['exercise_recommendations'] = {"steps": 0, "walking_km": 0}
            return image_dict
        except Exception as e:
            logger.error(f"Error getting image with analysis: {str(e)}")
            return None

    def get_user_images_with_analysis(self, user_id: int, skip: int = 0, limit: int = 20, filter_type: str = None, filter_value: str = None) -> List[Dict]:
        """
        Get all user images with their analysis data and presigned URLs valid for 1 day, only refreshed once per day.
        Supports filtering by date, week, or month. Only one filter is allowed at a time, with priority: date > week > month.
        """
        try:
            query = self.db.query(Image).filter(Image.owner_id == user_id)
            if filter_type == 'date' and filter_value:
                # Filter by specific date (YYYY-MM-DD)
                try:
                    date_obj = datetime.strptime(filter_value, '%Y-%m-%d')
                    next_day = date_obj + timedelta(days=1)
                    query = query.filter(Image.created_at >= date_obj, Image.created_at < next_day)
                except Exception:
                    pass  # Ignore invalid date
            elif filter_type == 'week' and filter_value:
                # Filter by ISO week (YYYY-Www)
                try:
                    match = re.match(r"(\d{4})-W(\d{2})", filter_value)
                    if match:
                        year, week = int(match.group(1)), int(match.group(2))
                        date_obj = datetime.strptime(f'{year}-W{week}-1', "%Y-W%W-%w")
                        next_week = date_obj + timedelta(weeks=1)
                        query = query.filter(Image.created_at >= date_obj, Image.created_at < next_week)
                except Exception:
                    pass  # Ignore invalid week
            elif filter_type == 'month' and filter_value:
                # Filter by month (YYYY-MM)
                try:
                    date_obj = datetime.strptime(filter_value, '%Y-%m')
                    if date_obj.month == 12:
                        next_month = date_obj.replace(year=date_obj.year+1, month=1)
                    else:
                        next_month = date_obj.replace(month=date_obj.month+1)
                    query = query.filter(Image.created_at >= date_obj, Image.created_at < next_month)
                except Exception:
                    pass  # Ignore invalid month
            images = query.offset(skip).limit(limit).all()
            now = datetime.now(timezone.utc)
            result = []
            for img in images:
                img_dict = img.to_dict()
                # Check if presigned_url is valid
                if img.presigned_url and img.presigned_url_expires_at and img.presigned_url_expires_at > now:
                    img_dict['file_url'] = img.presigned_url
                else:
                    # Generate new presigned URL for 1 day
                    presigned_url = self.s3_service.generate_presigned_url(img.s3_key, 86400)
                    img.presigned_url = presigned_url
                    img.presigned_url_expires_at = now + timedelta(seconds=86400)
                    self.db.commit()
                    img_dict['file_url'] = presigned_url
                result.append(img_dict)
            return result
        except Exception as e:
            logger.error(f"Error getting user images: {str(e)}")
            return []

    def get_image_with_presigned_url(self, image_id: int, user_id: int, expiration: int = 86400) -> Optional[Dict]:
        """Get image details with a presigned URL valid for 1 day, only refreshed once per day."""
        try:
            image = self.db.query(Image).filter(
                Image.id == image_id,
                Image.owner_id == user_id
            ).first()
            if not image:
                return None
            now = datetime.now(timezone.utc)
            if image.presigned_url and image.presigned_url_expires_at and image.presigned_url_expires_at > now:
                presigned_url = image.presigned_url
            else:
                presigned_url = self.s3_service.generate_presigned_url(image.s3_key, 86400)
                image.presigned_url = presigned_url
                image.presigned_url_expires_at = now + timedelta(seconds=86400)
                self.db.commit()
            image_data = image.to_dict()
            image_data['file_url'] = presigned_url
            return image_data
        except Exception as e:
            logger.error(f"Error getting image with presigned URL: {str(e)}")
            return None

    # Utility methods for testing
    async def test_s3_and_analysis(self, image_id: int, user_id: int) -> Dict:
        """Test method to check S3 access and analysis capabilities"""
        try:
            image = self.db.query(Image).filter(
                Image.id == image_id,
                Image.owner_id == user_id
            ).first()

            if not image:
                return {"error": "Image not found"}

            results = {
                "image_info": {
                    "id": image.id,
                    "s3_key": image.s3_key,
                    "file_url": image.file_url,
                    "content_type": image.content_type
                },
                "tests": {}
            }

            # Test S3 content access
            try:
                s3_content = self.s3_service.get_file_content(image.s3_key)
                results["tests"]["s3_content_access"] = {
                    "success": bool(s3_content),
                    "content_size": len(s3_content) if s3_content else 0
                }
            except Exception as e:
                results["tests"]["s3_content_access"] = {
                    "success": False,
                    "error": str(e)
                }

            # Test URL access
            try:
                response = requests.head(image.file_url, timeout=10)
                results["tests"]["url_access"] = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                }
            except Exception as e:
                results["tests"]["url_access"] = {
                    "success": False,
                    "error": str(e)
                }

            # Test LLM service
            try:
                llm_test = await self.llm_service.test_api_connection()
                results["tests"]["llm_service"] = {
                    "success": llm_test
                }
            except Exception as e:
                results["tests"]["llm_service"] = {
                    "success": False,
                    "error": str(e)
                }

            return results

        except Exception as e:
            logger.error(f"Error in test_s3_and_analysis: {str(e)}")
            return {"error": f"Test failed: {str(e)}"}