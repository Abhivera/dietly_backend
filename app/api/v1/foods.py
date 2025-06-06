from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.food import FoodItem
from app.schemas.food import FoodItemCreate, FoodItemUpdate, FoodItemResponse

router = APIRouter()

@router.get("/", response_model=List[FoodItemResponse])
def get_foods(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(FoodItem).filter(
        (FoodItem.is_predefined == True) | 
        (FoodItem.user_id == current_user.id)
    )
    
    if search:
        query = query.filter(FoodItem.name.ilike(f"%{search}%"))
    
    foods = query.offset(skip).limit(limit).all()
    return foods

@router.post("/", response_model=FoodItemResponse)
def create_food(
    food: FoodItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_food = FoodItem(**food.dict(), user_id=current_user.id)
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food

@router.put("/{food_id}", response_model=FoodItemResponse)
def update_food(
    food_id: UUID,
    food_update: FoodItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    food = db.query(FoodItem).filter(FoodItem.id == food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food item not found")
    
    if food.user_id != current_user.id and not food.is_predefined:
        raise HTTPException(status_code=403, detail="Not authorized to update this food item")
    
    update_data = food_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(food, field, value)
    
    db.commit()
    db.refresh(food)
    return food

@router.delete("/{food_id}")
def delete_food(
    food_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    food = db.query(FoodItem).filter(FoodItem.id == food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Food item not found")
    
    if food.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this food item")
    
    db.delete(food)
    db.commit()
    return {"message": "Food item deleted successfully"}

