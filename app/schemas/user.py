from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole, Gender

class UserBase(BaseModel):
    name: str
    email: EmailStr
    age: Optional[int] = None
    gender: Optional[Gender] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[Gender] = None
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    role: UserRole
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None