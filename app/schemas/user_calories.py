from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

class UserCaloriesBase(BaseModel):
    activity_date: date
    calories_burn: int = Field(..., ge=0, description="Calories burned must be non-negative")

class UserCaloriesCreate(UserCaloriesBase):
    pass

class UserCaloriesUpdate(BaseModel):
    activity_date: Optional[date] = None
    calories_burn: Optional[int] = Field(None, ge=0, description="Calories burned must be non-negative")

class UserCaloriesInDB(UserCaloriesBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserCaloriesResponse(UserCaloriesInDB):
    """Public user calories response"""
    pass

class UserCaloriesSummary(BaseModel):
    """Summary of user calories for a specific date range"""
    total_calories_burned: int
    average_calories_per_day: float
    date_range_start: date
    date_range_end: date
    entries_count: int 