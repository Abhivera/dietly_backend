from pydantic import BaseModel
from datetime import date
from uuid import UUID

class AnalyticsBase(BaseModel):
    date: date
    total_calories_in: int = 0
    total_calories_out: int = 0
    net_calories: int = 0

class AnalyticsResponse(AnalyticsBase):
    id: UUID
    user_id: UUID
    
    class Config:
        from_attributes = True

class DailyAnalytics(BaseModel):
    date: date
    calories_consumed: int
    calories_burned: int
    net_calories: int
    meals_count: int
    exercises_count: int

class WeeklyAnalytics(BaseModel):
    week_start: date
    week_end: date
    avg_calories_in: float
    avg_calories_out: float
    avg_net_calories: float
    total_meals: int
    total_exercises: int
    daily_breakdown: list[DailyAnalytics]