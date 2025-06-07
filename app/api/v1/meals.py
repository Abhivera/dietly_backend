from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.meal import Meal, MealItem
from app.models.food import FoodItem
from app.schemas.meal import (
    MealCreate, 
    MealUpdate, 
    MealResponse, 
    MealDetailResponse
)

router = APIRouter()

@router.post("/", response_model=MealDetailResponse)
def create_meal(
    meal: MealCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new meal with meal items"""
    
    # Create the meal
    db_meal = Meal(
        user_id=current_user.id,
        meal_date=meal.meal_date,
        meal_time=meal.meal_time,
        image_url=meal.image_url
    )
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    
    # Add meal items if provided
    total_calories = 0
    for meal_item_data in meal.meal_items:
        # Verify food item exists and user has access
        food_item = db.query(FoodItem).filter(
            FoodItem.id == meal_item_data.food_item_id
        ).filter(
            (FoodItem.is_predefined == True) | 
            (FoodItem.user_id == current_user.id)
        ).first()
        
        if not food_item:
            db.rollback()
            raise HTTPException(
                status_code=404, 
                detail=f"Food item {meal_item_data.food_item_id} not found or not accessible"
            )
        
        db_meal_item = MealItem(
            meal_id=db_meal.id,
            food_item_id=meal_item_data.food_item_id,
            quantity=meal_item_data.quantity
        )
        db.add(db_meal_item)
        
        # Calculate calories
        total_calories += food_item.calories * meal_item_data.quantity
    
    db.commit()
    
    # Fetch the complete meal with items
    meal_with_items = db.query(Meal).options(
        joinedload(Meal.meal_items).joinedload(MealItem.food_item)
    ).filter(Meal.id == db_meal.id).first()
    
    # Add total calories to response
    meal_with_items.total_calories = total_calories
    
    return meal_with_items

@router.get("/{user_id}", response_model=List[MealDetailResponse])
def get_user_meals(
    user_id: UUID,
    meal_date: Optional[date] = Query(None, description="Filter by specific date"),
    start_date: Optional[date] = Query(None, description="Filter from start date"),
    end_date: Optional[date] = Query(None, description="Filter to end date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get meals for a specific user with optional date filtering"""
    
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to view this user's meals"
        )
    
    # Build query
    query = db.query(Meal).options(
        joinedload(Meal.meal_items).joinedload(MealItem.food_item)
    ).filter(Meal.user_id == user_id)
    
    # Apply date filters
    if meal_date:
        query = query.filter(Meal.meal_date == meal_date)
    else:
        if start_date:
            query = query.filter(Meal.meal_date >= start_date)
        if end_date:
            query = query.filter(Meal.meal_date <= end_date)
    
    # Order by date and time (most recent first)
    query = query.order_by(Meal.meal_date.desc(), Meal.meal_time.desc())
    
    meals = query.offset(skip).limit(limit).all()
    
    # Calculate total calories for each meal
    for meal in meals:
        total_calories = 0
        for meal_item in meal.meal_items:
            total_calories += meal_item.food_item.calories * meal_item.quantity
        meal.total_calories = total_calories
    
    return meals

@router.get("/meal/{meal_id}", response_model=MealDetailResponse)
def get_meal(
    meal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific meal by ID"""
    
    meal = db.query(Meal).options(
        joinedload(Meal.meal_items).joinedload(MealItem.food_item)
    ).filter(Meal.id == meal_id).first()
    
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    if meal.user_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to view this meal"
        )
    
    # Calculate total calories
    total_calories = 0
    for meal_item in meal.meal_items:
        total_calories += meal_item.food_item.calories * meal_item.quantity
    meal.total_calories = total_calories
    
    return meal

@router.put("/{meal_id}", response_model=MealDetailResponse)
def update_meal(
    meal_id: UUID,
    meal_update: MealUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a meal and its items"""
    
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    if meal.user_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to update this meal"
        )
    
    # Update meal basic info
    update_data = meal_update.dict(exclude_unset=True)
    meal_items_data = update_data.pop('meal_items', None)
    
    for field, value in update_data.items():
        setattr(meal, field, value)
    
    # Update meal items if provided
    if meal_items_data is not None:
        # Delete existing meal items
        db.query(MealItem).filter(MealItem.meal_id == meal_id).delete()
        
        # Add new meal items
        for meal_item_data in meal_items_data:
            # Verify food item exists and user has access
            food_item = db.query(FoodItem).filter(
                FoodItem.id == meal_item_data['food_item_id']
            ).filter(
                (FoodItem.is_predefined == True) | 
                (FoodItem.user_id == current_user.id)
            ).first()
            
            if not food_item:
                db.rollback()
                raise HTTPException(
                    status_code=404,
                    detail=f"Food item {meal_item_data['food_item_id']} not found or not accessible"
                )
            
            db_meal_item = MealItem(
                meal_id=meal_id,
                food_item_id=meal_item_data['food_item_id'],
                quantity=meal_item_data['quantity']
            )
            db.add(db_meal_item)
    
    db.commit()
    
    # Fetch updated meal with items
    updated_meal = db.query(Meal).options(
        joinedload(Meal.meal_items).joinedload(MealItem.food_item)
    ).filter(Meal.id == meal_id).first()
    
    # Calculate total calories
    total_calories = 0
    for meal_item in updated_meal.meal_items:
        total_calories += meal_item.food_item.calories * meal_item.quantity
    updated_meal.total_calories = total_calories
    
    return updated_meal

@router.delete("/{meal_id}")
def delete_meal(
    meal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a meal and all its items"""
    
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    if meal.user_id != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to delete this meal"
        )
    
    # Delete meal items first (cascade should handle this, but being explicit)
    db.query(MealItem).filter(MealItem.meal_id == meal_id).delete()
    
    # Delete the meal
    db.delete(meal)
    db.commit()
    
    return {"message": "Meal deleted successfully"}

@router.get("/today/{user_id}", response_model=List[MealDetailResponse])
def get_today_meals(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get today's meals for a user"""
    
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to view this user's meals"
        )
    
    today = date.today()
    
    meals = db.query(Meal).options(
        joinedload(Meal.meal_items).joinedload(MealItem.food_item)
    ).filter(
        Meal.user_id == user_id,
        Meal.meal_date == today
    ).order_by(Meal.meal_time.asc()).all()
    
    # Calculate total calories for each meal
    for meal in meals:
        total_calories = 0
        for meal_item in meal.meal_items:
            total_calories += meal_item.food_item.calories * meal_item.quantity
        meal.total_calories = total_calories
    
    return meals

@router.get("/stats/{user_id}")
def get_meal_stats(
    user_id: UUID,
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get meal statistics for a user"""
    
    if current_user.id != user_id:
        raise HTTPException(
            status_code=403, 
            detail="Not authorized to view this user's data"
        )
    
    from datetime import timedelta
    start_date = date.today() - timedelta(days=days-1)
    
    meals = db.query(Meal).options(
        joinedload(Meal.meal_items).joinedload(MealItem.food_item)
    ).filter(
        Meal.user_id == user_id,
        Meal.meal_date >= start_date
    ).all()
    
    total_meals = len(meals)
    total_calories = 0
    daily_calories = {}
    
    for meal in meals:
        meal_calories = 0
        for meal_item in meal.meal_items:
            meal_calories += meal_item.food_item.calories * meal_item.quantity
        
        total_calories += meal_calories
        meal_date_str = meal.meal_date.isoformat()
        
        if meal_date_str not in daily_calories:
            daily_calories[meal_date_str] = 0
        daily_calories[meal_date_str] += meal_calories
    
    avg_calories_per_day = total_calories / days if days > 0 else 0
    avg_calories_per_meal = total_calories / total_meals if total_meals > 0 else 0
    
    return {
        "total_meals": total_meals,
        "total_calories": total_calories,
        "avg_calories_per_day": round(avg_calories_per_day, 2),
        "avg_calories_per_meal": round(avg_calories_per_meal, 2),
        "daily_calories": daily_calories,
        "days_analyzed": days
    }