from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_superuser
from app.schemas.user import UserResponse, UserUpdate
from app.models.user import User
from app.services.s3_service import S3Service

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Update user fields
    update_data = user_update.dict(exclude_unset=True)
    
    if "password" in update_data:
        from app.core.security import get_password_hash
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user

# @router.patch("/me/avatar", response_model=UserResponse)
# def update_user_avatar(
#     avatar_url: str = Body(..., embed=True),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     current_user.avatar_url = avatar_url
#     db.commit()
#     db.refresh(current_user)
#     return current_user

@router.post("/me/avatar", response_model=UserResponse)
def upload_user_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    s3_service = S3Service()
    # Read file content into BytesIO
    file_content = file.file.read()
    from io import BytesIO
    file_obj = BytesIO(file_content)
    # Upload to S3 with public access
    upload_result = s3_service.upload_file_with_public_access(file_obj, current_user.id, file.filename)
    if not upload_result.get('success'):
        raise HTTPException(status_code=500, detail=upload_result.get('error', 'Upload failed'))
    # Update user's avatar_url
    current_user.avatar_url = upload_result['file_url']
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/", response_model=List[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """
    Hard delete a user and related data.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"success": True, "message": f"User {user_id} and related data deleted."}
