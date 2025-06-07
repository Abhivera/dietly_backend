from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date, time
from uuid import UUID

class MealItemCreate(BaseModel):
    food_item_id: UUID
    quantity: int

class MealItemUpdate(BaseModel):
    food_item_id: Optional[UUID] = None
    quantity: Optional[int] = None

class MealItemResponse(BaseModel):
    id: UUID
    meal_id: UUID
    food_item_id: UUID
    quantity: int
    
    class Config:
        from_attributes = True

class MealItemWithFood(MealItemResponse):
    food_item: "FoodItemResponse"
    
    class Config:
        from_attributes = True

class MealBase(BaseModel):
    meal_date: date
    meal_time: time
    image_url: Optional[str] = None

class MealCreate(MealBase):
    meal_items: List[MealItemCreate] = []

class MealUpdate(BaseModel):
    meal_date: Optional[date] = None
    meal_time: Optional[time] = None
    image_url: Optional[str] = None
    meal_items: Optional[List[MealItemCreate]] = None

class MealResponse(MealBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class MealDetailResponse(MealResponse):
    meal_items: List[MealItemWithFood] = []
    total_calories: Optional[int] = None
    
    class Config:
        from_attributes = True

# Import here to avoid circular imports
from app.schemas.food import FoodItemResponse
MealItemWithFood.model_rebuild()