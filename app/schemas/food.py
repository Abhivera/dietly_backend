from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class FoodItemBase(BaseModel):
    name: str
    calories: int
    image_url: Optional[str] = None
    is_predefined: Optional[bool] = False

class FoodItemCreate(FoodItemBase):
    pass

class FoodItemUpdate(BaseModel):
    name: Optional[str] = None
    calories: Optional[int] = None
    image_url: Optional[str] = None

class FoodItemResponse(FoodItemBase):
    id: UUID
    is_predefined: bool
    user_id: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True