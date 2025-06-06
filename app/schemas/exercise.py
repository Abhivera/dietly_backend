from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from uuid import UUID

class ExerciseItemBase(BaseModel):
    name: str
    duration_mins: int
    calories_burnt: int

class ExerciseItemCreate(ExerciseItemBase):
    pass

class ExerciseItemUpdate(BaseModel):
    name: Optional[str] = None
    duration_mins: Optional[int] = None
    calories_burnt: Optional[int] = None

class ExerciseItemResponse(ExerciseItemBase):
    id: UUID
    is_predefined: bool
    user_id: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserExerciseCreate(BaseModel):
    exercise_item_id: UUID
    date: datetime
    duration_mins: int

class UserExerciseResponse(BaseModel):
    id: UUID
    user_id: UUID
    exercise_item_id: UUID
    date: datetime
    duration_mins: int
    exercise_item: ExerciseItemResponse
    
    class Config:
        from_attributes = True