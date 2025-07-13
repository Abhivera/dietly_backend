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
    UserCaloriesSummary,
    ActivityCalories
)
from app.models.user import User
from app.models.user_calories import UserCalories

router = APIRouter()

def calculate_total_calories(calories_burned: List[ActivityCalories]) -> int:
    """Calculate total calories from activities list"""
    total = 0
    for activity in calories_burned:
        try:
            total += int(activity.calories)
        except ValueError:
            # Skip invalid calorie values
            continue
    return total

def create_activities_summary(calories_entries: List[UserCalories]) -> dict:
    """Create summary of calories by activity type"""
    activities_summary = {}
    
    for entry in calories_entries:
        if entry.calories_burned:
            for activity in entry.calories_burned:
                activity_name = activity.get("activity_name", "Unknown")
                try:
                    calories = int(activity.get("calories", 0))
                    activities_summary[activity_name] = activities_summary.get(activity_name, 0) + calories
                except (ValueError, TypeError):
                    continue
    
    return activities_summary

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
    
    # Convert activities to JSON format
    activities_json = [activity.dict() for activity in calories_data.calories_burned]
    
    db_calories = UserCalories(
        user_id=current_user.id,
        activity_date=calories_data.activity_date,
        calories_burned=activities_json
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
    """
    Update a specific calorie entry
    
    This endpoint allows you to update an existing calorie entry. You can update:
    - The activity date
    - The list of activities and calories burned
    
    **Validation Rules:**
    - Activity names cannot be empty or exceed 100 characters
    - Calories must be valid numbers between 0 and 10,000
    - No duplicate activity names allowed
    - Total daily calories cannot exceed 5,000
    - Activity date cannot be in the future
    
    **Example Request Body:**
    ```json
    {
      "activity_date": "2024-01-15",
      "calories_burned": [
        {
          "activity_name": "running",
          "calories": "250"
        },
        {
          "activity_name": "cycling", 
          "calories": "180"
        }
      ]
    }
    ```
    """
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
    
    # Robustly handle both dicts and Pydantic models for calories_burned
    if "calories_burned" in update_data:
        new_activities = []
        for activity in update_data["calories_burned"]:
            if hasattr(activity, "dict"):
                new_activities.append(activity.dict())
            elif isinstance(activity, dict):
                new_activities.append(activity)
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid activity format in calories_burned"
                )
        update_data["calories_burned"] = new_activities
    
    try:
        for field, value in update_data.items():
            setattr(calories, field, value)
        
        db.commit()
        db.refresh(calories)
        return calories
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update calorie entry: {str(e)}"
        )

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
    
    # Get all entries in the date range
    calories_entries = db.query(UserCalories).filter(
        UserCalories.user_id == current_user.id,
        UserCalories.activity_date >= start_date,
        UserCalories.activity_date <= end_date
    ).all()
    
    entries_count = len(calories_entries)
    
    # Calculate total calories from all activities
    total_calories = 0
    for entry in calories_entries:
        if entry.calories_burned:
            for activity in entry.calories_burned:
                try:
                    total_calories += int(activity.get("calories", 0))
                except (ValueError, TypeError):
                    continue
    
    # Calculate average
    average_calories = total_calories / entries_count if entries_count > 0 else 0
    
    # Create activities summary
    activities_summary = create_activities_summary(calories_entries)
    
    return UserCaloriesSummary(
        total_calories_burned=total_calories,
        average_calories_per_day=average_calories,
        date_range_start=start_date,
        date_range_end=end_date,
        entries_count=entries_count,
        activities_summary=activities_summary
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
    
    # Get all entries in the date range
    calories_entries = db.query(UserCalories).filter(
        UserCalories.user_id == current_user.id,
        UserCalories.activity_date >= start_date,
        UserCalories.activity_date <= end_date
    ).all()
    
    entries_count = len(calories_entries)
    
    # Calculate total calories from all activities
    total_calories = 0
    for entry in calories_entries:
        if entry.calories_burned:
            for activity in entry.calories_burned:
                try:
                    total_calories += int(activity.get("calories", 0))
                except (ValueError, TypeError):
                    continue
    
    # Calculate average
    average_calories = total_calories / entries_count if entries_count > 0 else 0
    
    # Create activities summary
    activities_summary = create_activities_summary(calories_entries)
    
    return UserCaloriesSummary(
        total_calories_burned=total_calories,
        average_calories_per_day=average_calories,
        date_range_start=start_date,
        date_range_end=end_date,
        entries_count=entries_count,
        activities_summary=activities_summary
    ) 