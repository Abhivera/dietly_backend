from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import os

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.analytics import AnalyticsResponse
from app.core.config import settings  # Ensure settings.UPLOAD_DIR is defined
from app.utils.file_upload import FileUploadHelper  # Custom helper for saving/resizing images

router = APIRouter()

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

@router.get("/{user_id}/analytics", response_model=List[AnalyticsResponse])
def get_user_analytics(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this data")
    
    from app.models.analytics import Analytics
    analytics = db.query(Analytics).filter(Analytics.user_id == user_id).all()
    return analytics

@router.post("/{user_id}/upload-avatar")
def upload_user_avatar(
    user_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

        # Save uploaded image
        file_path = FileUploadHelper.save_image(file, settings.UPLOAD_DIR)

        # Resize image for avatar
        FileUploadHelper.resize_image(file_path, max_width=300, max_height=300)

        # Update user with avatar URL
        user.avatar_url = f"/uploads/{os.path.basename(file_path)}"
        db.commit()

        return {"message": "Avatar uploaded successfully", "avatar_url": user.avatar_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading avatar: {str(e)}")
