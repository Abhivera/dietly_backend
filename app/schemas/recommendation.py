from pydantic import BaseModel
from typing import Optional, Union
from datetime import date, datetime
from uuid import UUID
from app.models.recommendation import RecommendationType
from app.schemas.food import FoodItemResponse
from app.schemas.exercise import ExerciseItemResponse

class RecommendationResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: RecommendationType
    recommended_item_id: UUID
    date: date
    reason: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True