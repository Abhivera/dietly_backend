from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID
import os

from app.core.database import get_db
from app.core.config import settings
from app.helpers.file_upload import FileUploadHelper  # Ensure this helper exists
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.vlog import Vlog, VlogComment, VlogLike
from app.schemas.vlog import (
    VlogCreate, VlogUpdate, VlogResponse, VlogCommentCreate, VlogCommentResponse
)

router = APIRouter()


@router.post("/", response_model=VlogResponse)
def create_vlog(
    vlog: VlogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_vlog = Vlog(**vlog.dict(), user_id=current_user.id)
    db.add(db_vlog)
    db.commit()
    db.refresh(db_vlog)
    return db_vlog


@router.get("/", response_model=List[VlogResponse])
def get_vlogs(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    vlogs = db.query(Vlog).offset(skip).limit(limit).all()

    for vlog in vlogs:
        vlog.likes_count = db.query(func.count(VlogLike.id)).filter(VlogLike.vlog_id == vlog.id).scalar() or 0
        vlog.is_liked = db.query(VlogLike).filter(
            VlogLike.vlog_id == vlog.id,
            VlogLike.user_id == current_user.id
        ).first() is not None

    return vlogs


@router.get("/{vlog_id}", response_model=VlogResponse)
def get_vlog(
    vlog_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    vlog = db.query(Vlog).filter(Vlog.id == vlog_id).first()
    if not vlog:
        raise HTTPException(status_code=404, detail="Vlog not found")

    vlog.likes_count = db.query(func.count(VlogLike.id)).filter(VlogLike.vlog_id == vlog.id).scalar() or 0
    vlog.is_liked = db.query(VlogLike).filter(
        VlogLike.vlog_id == vlog.id,
        VlogLike.user_id == current_user.id
    ).first() is not None

    return vlog


@router.post("/{vlog_id}/comments", response_model=VlogCommentResponse)
def create_vlog_comment(
    vlog_id: UUID,
    comment: VlogCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    vlog = db.query(Vlog).filter(Vlog.id == vlog_id).first()
    if not vlog:
        raise HTTPException(status_code=404, detail="Vlog not found")

    db_comment = VlogComment(
        vlog_id=vlog_id,
        user_id=current_user.id,
        **comment.dict()
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


@router.post("/{vlog_id}/like")
def like_vlog(
    vlog_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    vlog = db.query(Vlog).filter(Vlog.id == vlog_id).first()
    if not vlog:
        raise HTTPException(status_code=404, detail="Vlog not found")

    existing_like = db.query(VlogLike).filter(
        VlogLike.vlog_id == vlog_id,
        VlogLike.user_id == current_user.id
    ).first()

    if existing_like:
        raise HTTPException(status_code=400, detail="Already liked")

    db_like = VlogLike(vlog_id=vlog_id, user_id=current_user.id)
    db.add(db_like)
    db.commit()

    return {"message": "Vlog liked successfully"}


@router.delete("/{vlog_id}/like")
def unlike_vlog(
    vlog_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    existing_like = db.query(VlogLike).filter(
        VlogLike.vlog_id == vlog_id,
        VlogLike.user_id == current_user.id
    ).first()

    if not existing_like:
        raise HTTPException(status_code=404, detail="Like not found")

    db.delete(existing_like)
    db.commit()

    return {"message": "Vlog unliked successfully"}


@router.post("/{vlog_id}/upload-image")
def upload_vlog_image(
    vlog_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    vlog = db.query(Vlog).filter(Vlog.id == vlog_id).first()
    if not vlog:
        raise HTTPException(status_code=404, detail="Vlog not found")

    if vlog.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this vlog")

    file_path = FileUploadHelper.save_image(file, settings.UPLOAD_DIR)
    FileUploadHelper.resize_image(file_path, max_width=1200, max_height=800)

    vlog.image_url = f"/uploads/{os.path.basename(file_path)}"
    db.commit()

    return {"message": "Image uploaded successfully", "image_url": vlog.image_url}
