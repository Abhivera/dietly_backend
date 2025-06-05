from pydantic import BaseModel
from typing import List, Optional
from datetime import date, time, datetime
from uuid import UUID
from app.schemas.food import FoodItemResponse

class MealItemBase(BaseModel):
    food_item_id: UUID
    quantity: int

class MealItemCreate(MealItemBase):
    pass

class MealItemResponse(MealItemBase):
    id: UUID
    meal_id: UUID
    food_item: FoodItemResponse
    
    class Config:
        from_attributes = True

class MealBase(BaseModel):
    meal_date: date
    meal_time: time
    image_url: Optional[str] = None

class MealCreate(MealBase):
    meal_items: List[MealItemCreate]

class MealUpdate(BaseModel):
    meal_date: Optional[date] = None
    meal_time: Optional[time] = None
    image_url: Optional[str] = None
    meal_items: Optional[List[MealItemCreate]] = None

class MealResponse(MealBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    meal_items: List[MealItemResponse] = []
    
    class Config:
        from_attributes = True