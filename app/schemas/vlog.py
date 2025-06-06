from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.schemas.user import UserResponse

class VlogBase(BaseModel):
    title: str
    image_url: str
    description: Optional[str] = None

class VlogCreate(VlogBase):
    pass

class VlogUpdate(BaseModel):
    title: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None

class VlogCommentCreate(BaseModel):
    comment: str
    parent_id: Optional[UUID] = None

class VlogCommentResponse(BaseModel):
    id: UUID
    vlog_id: UUID
    user_id: UUID
    comment: str
    parent_id: Optional[UUID] = None
    created_at: datetime
    user: UserResponse
    replies: List['VlogCommentResponse'] = []
    
    class Config:
        from_attributes = True

class VlogResponse(VlogBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    user: UserResponse
    comments: List[VlogCommentResponse] = []
    likes_count: int = 0
    is_liked: bool = False
    
    class Config:
        from_attributes = True