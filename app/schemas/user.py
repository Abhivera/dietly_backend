from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserCreateGoogle(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    google_id: str
    avatar_url: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    google_id: Optional[str] = None
    avatar_url: Optional[str] = None
    provider: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserResponse(UserInDB):
    pass