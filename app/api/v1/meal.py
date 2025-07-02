from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.image_service import ImageService
from app.api.deps import get_current_user
from typing import Dict

router = APIRouter()

@router.get("/", summary="Get meal, calorie, and exercise summary", tags=["meal"])
async def get_meal_summary(
    date: str = None,  # format: YYYY-MM-DD
    week: str = None,  # format: YYYY-Www
    month: str = None, # format: YYYY-MM
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Dict:
    """
    Get daily, weekly, or monthly summary of meals, calories, and exercise for the current user.
    Only images marked as is_meal=True are considered.
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
            current_user.id, 0, 10000, filter_type, filter_value
        )
        # Only consider images marked as meal
        meal_images = [img for img in images if img.get('analysis', {}).get('is_meal')]
        total_meals = len(meal_images)
        total_calories = sum(img.get('analysis', {}).get('calories', 0) or 0 for img in meal_images)
        total_steps = sum(img.get('analysis', {}).get('exercise_recommendations', {}).get('steps', 0) or 0 for img in meal_images)
        total_km = sum(img.get('analysis', {}).get('exercise_recommendations', {}).get('walking_km', 0) or 0 for img in meal_images)
        return {
            "total_meals": total_meals,
            "total_calories": total_calories,
            "total_exercise": {
                "steps": total_steps,
                "walking_km": total_km
            },
            "meals": meal_images
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve meal summary: {str(e)}") 