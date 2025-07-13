from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import re

class ActivityCalories(BaseModel):
    activity_name: str = Field(..., min_length=1, max_length=100, description="Name of the activity")
    calories: str = Field(..., description="Calories burned for this activity")

    @validator('activity_name')
    def validate_activity_name(cls, v):
        if not v.strip():
            raise ValueError('Activity name cannot be empty')
        if len(v.strip()) > 100:
            raise ValueError('Activity name cannot exceed 100 characters')
        return v.strip()

    @validator('calories')
    def validate_calories(cls, v):
        if not v.strip():
            raise ValueError('Calories value cannot be empty')
        
        # Check if it's a valid number
        try:
            calories_int = int(v)
            if calories_int < 0:
                raise ValueError('Calories cannot be negative')
            if calories_int > 10000:  # Reasonable upper limit
                raise ValueError('Calories value seems too high (max 10000)')
        except ValueError as e:
            if 'negative' in str(e) or 'too high' in str(e):
                raise e
            raise ValueError('Calories must be a valid number')
        
        return v

class UserCaloriesBase(BaseModel):
    activity_date: date
    calories_burned: List[ActivityCalories] = Field(..., description="List of activities with calories burned")

    @validator('calories_burned')
    def validate_calories_burned(cls, v):
        if not v:
            raise ValueError('At least one activity must be provided')
        
        # Check for duplicate activity names
        activity_names = [activity.activity_name.lower() for activity in v]
        if len(activity_names) != len(set(activity_names)):
            raise ValueError('Duplicate activity names are not allowed')
        
        # Check total calories limit
        total_calories = 0
        for activity in v:
            try:
                total_calories += int(activity.calories)
            except ValueError:
                continue
        
        if total_calories > 5000:  # Daily limit
            raise ValueError('Total daily calories burned cannot exceed 5000')
        
        return v

    @validator('activity_date')
    def validate_activity_date(cls, v):
        if v > date.today():
            raise ValueError('Activity date cannot be in the future')
        return v

class UserCaloriesCreate(UserCaloriesBase):
    pass

class UserCaloriesUpdate(BaseModel):
    activity_date: Optional[date] = None
    calories_burned: Optional[List[ActivityCalories]] = Field(None, description="List of activities with calories burned")

    @validator('calories_burned')
    def validate_calories_burned(cls, v):
        if v is not None:
            if not v:
                raise ValueError('At least one activity must be provided')
            
            # Check for duplicate activity names
            activity_names = [activity.activity_name.lower() for activity in v]
            if len(activity_names) != len(set(activity_names)):
                raise ValueError('Duplicate activity names are not allowed')
            
            # Check total calories limit
            total_calories = 0
            for activity in v:
                try:
                    total_calories += int(activity.calories)
                except ValueError:
                    continue
            
            if total_calories > 5000:  # Daily limit
                raise ValueError('Total daily calories burned cannot exceed 5000')
        
        return v

    @validator('activity_date')
    def validate_activity_date(cls, v):
        if v is not None and v > date.today():
            raise ValueError('Activity date cannot be in the future')
        return v

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
    activities_summary: Dict[str, int] = Field(..., description="Summary of calories by activity type") 