from typing import List, Optional
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.api.deps import get_current_user
from app.schemas.user_calories import (
    UserCaloriesCreate, 
    UserCaloriesUpdate, 
    UserCaloriesResponse, 
    UserCaloriesSummary
)
from app.models.user import User
from app.models.user_calories import UserCalories

router = APIRouter()

@router.post("/", response_model=UserCaloriesResponse)
def create_user_calories(
    calories_data: UserCaloriesCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new calorie entry for the current user"""
    # Check if entry already exists for this date
    existing_entry = db.query(UserCalories).filter(
        UserCalories.user_id == current_user.id,
        UserCalories.activity_date == calories_data.activity_date
    ).first()
    
    if existing_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Calorie entry already exists for date {calories_data.activity_date}"
        )
    
    db_calories = UserCalories(
        user_id=current_user.id,
        activity_date=calories_data.activity_date,
        calories_burn=calories_data.calories_burn
    )
    
    db.add(db_calories)
    db.commit()
    db.refresh(db_calories)
    return db_calories

@router.get("/", response_model=List[UserCaloriesResponse])
def get_user_calories(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get calorie entries for the current user with optional date filtering"""
    query = db.query(UserCalories).filter(UserCalories.user_id == current_user.id)
    
    if start_date:
        query = query.filter(UserCalories.activity_date >= start_date)
    
    if end_date:
        query = query.filter(UserCalories.activity_date <= end_date)
    
    calories = query.order_by(UserCalories.activity_date.desc()).offset(skip).limit(limit).all()
    return calories

@router.get("/{calories_id}", response_model=UserCaloriesResponse)
def get_user_calories_by_id(
    calories_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific calorie entry by ID"""
    calories = db.query(UserCalories).filter(
        UserCalories.id == calories_id,
        UserCalories.user_id == current_user.id
    ).first()
    
    if not calories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calorie entry not found"
        )
    
    return calories

@router.get("/date/{activity_date}", response_model=UserCaloriesResponse)
def get_user_calories_by_date(
    activity_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get calorie entry for a specific date"""
    calories = db.query(UserCalories).filter(
        UserCalories.user_id == current_user.id,
        UserCalories.activity_date == activity_date
    ).first()
    
    if not calories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No calorie entry found for date {activity_date}"
        )
    
    return calories

@router.put("/{calories_id}", response_model=UserCaloriesResponse)
def update_user_calories(
    calories_id: int,
    calories_update: UserCaloriesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a specific calorie entry"""
    calories = db.query(UserCalories).filter(
        UserCalories.id == calories_id,
        UserCalories.user_id == current_user.id
    ).first()
    
    if not calories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calorie entry not found"
        )
    
    update_data = calories_update.dict(exclude_unset=True)
    
    # If updating activity_date, check for conflicts
    if "activity_date" in update_data:
        existing_entry = db.query(UserCalories).filter(
            UserCalories.user_id == current_user.id,
            UserCalories.activity_date == update_data["activity_date"],
            UserCalories.id != calories_id
        ).first()
        
        if existing_entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Calorie entry already exists for date {update_data['activity_date']}"
            )
    
    for field, value in update_data.items():
        setattr(calories, field, value)
    
    db.commit()
    db.refresh(calories)
    return calories

@router.delete("/{calories_id}")
def delete_user_calories(
    calories_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific calorie entry"""
    calories = db.query(UserCalories).filter(
        UserCalories.id == calories_id,
        UserCalories.user_id == current_user.id
    ).first()
    
    if not calories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calorie entry not found"
        )
    
    db.delete(calories)
    db.commit()
    
    return {"success": True, "message": "Calorie entry deleted successfully"}

@router.get("/summary/range", response_model=UserCaloriesSummary)
def get_user_calories_summary(
    start_date: date = Query(..., description="Start date for summary"),
    end_date: date = Query(..., description="End date for summary"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary of calories burned in a date range"""
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before or equal to end date"
        )
    
    # Get total calories and count
    result = db.query(
        func.sum(UserCalories.calories_burn).label('total_calories'),
        func.count(UserCalories.id).label('entries_count')
    ).filter(
        UserCalories.user_id == current_user.id,
        UserCalories.activity_date >= start_date,
        UserCalories.activity_date <= end_date
    ).first()
    
    total_calories = result.total_calories or 0
    entries_count = result.entries_count or 0
    
    # Calculate average
    average_calories = total_calories / entries_count if entries_count > 0 else 0
    
    return UserCaloriesSummary(
        total_calories_burned=total_calories,
        average_calories_per_day=average_calories,
        date_range_start=start_date,
        date_range_end=end_date,
        entries_count=entries_count
    )

@router.get("/summary/recent", response_model=UserCaloriesSummary)
def get_recent_calories_summary(
    days: int = Query(7, ge=1, le=365, description="Number of recent days to summarize"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary of calories burned in the last N days"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    
    # Get total calories and count
    result = db.query(
        func.sum(UserCalories.calories_burn).label('total_calories'),
        func.count(UserCalories.id).label('entries_count')
    ).filter(
        UserCalories.user_id == current_user.id,
        UserCalories.activity_date >= start_date,
        UserCalories.activity_date <= end_date
    ).first()
    
    total_calories = result.total_calories or 0
    entries_count = result.entries_count or 0
    
    # Calculate average
    average_calories = total_calories / entries_count if entries_count > 0 else 0
    
    return UserCaloriesSummary(
        total_calories_burned=total_calories,
        average_calories_per_day=average_calories,
        date_range_start=start_date,
        date_range_end=end_date,
        entries_count=entries_count
    ) 