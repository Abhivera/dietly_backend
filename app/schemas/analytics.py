from pydantic import BaseModel
from datetime import date
from uuid import UUID

class AnalyticsResponse(BaseModel):
    id: UUID
    user_id: UUID
    date: date
    total_calories_in: int
    total_calories_out: int
    net_calories: int
    
    class Config:
        from_attributes = True

class AnalyticsSummary(BaseModel):
    total_days: int
    avg_calories_in: float
    avg_calories_out: float
    avg_net_calories: float
    total_calories_in: int
    total_calories_out: int
