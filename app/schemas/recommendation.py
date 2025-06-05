from pydantic import BaseModel
from typing import Optional, Union
from datetime import date, datetime
from uuid import UUID
from app.models.recommendation import RecommendationType
from app.schemas.food import FoodItemResponse
from app.schemas.exercise import ExerciseItemResponse

class RecommendationBase(BaseModel):
    type: RecommendationType
    recommended_item_id: UUID
    date: date
    reason: Optional[str] = None

class RecommendationCreate(RecommendationBase):
    pass

class RecommendationResponse(RecommendationBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class RecommendationWithItem(RecommendationResponse):
    recommended_item: Optional[Union[FoodItemResponse, ExerciseItemResponse]] = None