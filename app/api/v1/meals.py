import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.meal import Meal, MealItem
from app.schemas.meal import MealCreate, MealUpdate, MealResponse
from fastapi import UploadFile, File
from app.utils.helpers import FileUploadHelper
from app.core.config import settings

router = APIRouter()

@router.post("/", response_model=MealResponse)
def create_meal(
    meal: MealCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_meal = Meal(
        user_id=current_user.id,
        meal_date=meal.meal_date,
        meal_time=meal.meal_time,
        image_url=meal.image_url
    )
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    
    # Add meal items
    for meal_item_data in meal.meal_items:
        db_meal_item = MealItem(
            meal_id=db_meal.id,
            **meal_item_data.dict()
        )
        db.add(db_meal_item)
    
    db.commit()
    db.refresh(db_meal)
    return db_meal

@router.get("/{user_id}", response_model=List[MealResponse])
def get_user_meals(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this data")
    
    meals = db.query(Meal).filter(Meal.user_id == user_id).all()
    return meals

@router.get("/meal/{meal_id}", response_model=MealResponse)
def get_meal(
    meal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    if meal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this meal")
    
    return meal

@router.put("/{meal_id}", response_model=MealResponse)
def update_meal(
    meal_id: UUID,
    meal_update: MealUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    if meal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this meal")
    
    update_data = meal_update.dict(exclude_unset=True)
    meal_items_data = update_data.pop('meal_items', None)
    
    for field, value in update_data.items():
        setattr(meal, field, value)
    
    if meal_items_data is not None:
        # Delete existing meal items
        db.query(MealItem).filter(MealItem.meal_id == meal_id).delete()
        
        # Add new meal items
        for meal_item_data in meal_items_data:
            db_meal_item = MealItem(meal_id=meal_id, **meal_item_data)
            db.add(db_meal_item)
    
    db.commit()
    db.refresh(meal)
    return meal

@router.delete("/{meal_id}")
def delete_meal(
    meal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    if meal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this meal")
    
    db.delete(meal)
    db.commit()
    return {"message": "Meal deleted successfully"}
@router.post("/{meal_id}/upload-image")
def upload_meal_image(
    meal_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    meal = db.query(Meal).filter(Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    if meal.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this meal")
    
    # Save uploaded image
    file_path = FileUploadHelper.save_image(file, settings.UPLOAD_DIR)
    
    # Resize image
    FileUploadHelper.resize_image(file_path)
    
    # Update meal with image URL
    meal.image_url = f"/uploads/{os.path.basename(file_path)}"
    db.commit()
    
    return {"message": "Image uploaded successfully", "image_url": meal.image_url}