from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.exercise import ExerciseItem, UserExercise
from app.schemas.exercise import (
    ExerciseItemCreate, ExerciseItemUpdate, ExerciseItemResponse,
    UserExerciseCreate, UserExerciseResponse
)

router = APIRouter()

@router.get("/", response_model=List[ExerciseItemResponse])
def get_exercises(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(ExerciseItem).filter(
        (ExerciseItem.is_predefined == True) | 
        (ExerciseItem.user_id == current_user.id)
    )
    
    if search:
        query = query.filter(ExerciseItem.name.ilike(f"%{search}%"))
    
    exercises = query.offset(skip).limit(limit).all()
    return exercises

@router.post("/", response_model=ExerciseItemResponse)
def create_exercise(
    exercise: ExerciseItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_exercise = ExerciseItem(**exercise.dict(), user_id=current_user.id)
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise

@router.put("/{exercise_id}", response_model=ExerciseItemResponse)
def update_exercise(
    exercise_id: UUID,
    exercise_update: ExerciseItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    exercise = db.query(ExerciseItem).filter(ExerciseItem.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    if exercise.user_id != current_user.id and not exercise.is_predefined:
        raise HTTPException(status_code=403, detail="Not authorized to update this exercise")
    
    update_data = exercise_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(exercise, field, value)
    
    db.commit()
    db.refresh(exercise)
    return exercise

@router.delete("/{exercise_id}")
def delete_exercise(
    exercise_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    exercise = db.query(ExerciseItem).filter(ExerciseItem.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    if exercise.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this exercise")
    
    db.delete(exercise)
    db.commit()
    return {"message": "Exercise deleted successfully"}

# User Exercise Activity endpoints
@router.post("/user-exercises", response_model=UserExerciseResponse)
def create_user_exercise(
    user_exercise: UserExerciseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_user_exercise = UserExercise(**user_exercise.dict(), user_id=current_user.id)
    db.add(db_user_exercise)
    db.commit()
    db.refresh(db_user_exercise)
    return db_user_exercise

@router.get("/user-exercises/{user_id}", response_model=List[UserExerciseResponse])
def get_user_exercises(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this data")
    
    user_exercises = db.query(UserExercise).filter(UserExercise.user_id == user_id).all()
    return user_exercises