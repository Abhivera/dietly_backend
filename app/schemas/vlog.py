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

class VlogCommentBase(BaseModel):
    comment: str
    parent_id: Optional[UUID] = None

class VlogCommentCreate(VlogCommentBase):
    pass

class VlogCommentResponse(VlogCommentBase):
    id: UUID
    vlog_id: UUID
    user_id: UUID
    user: UserResponse
    created_at: datetime
    replies: List["VlogCommentResponse"] = []
    
    class Config:
        from_attributes = True

class VlogLikeResponse(BaseModel):
    id: UUID
    vlog_id: UUID
    user_id: UUID
    user: UserResponse
    
    class Config:
        from_attributes = True

class VlogResponse(VlogBase):
    id: UUID
    user_id: UUID
    user: UserResponse
    created_at: datetime
    comments: List[VlogCommentResponse] = []
    likes: List[VlogLikeResponse] = []
    likes_count: int = 0
    comments_count: int = 0
    
    class Config:
        from_attributes = True

# For forward reference
VlogCommentResponse.model_rebuild()