from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base  # Ensure this import is correct
import uuid
import enum

class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"

class Gender(enum.Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    avatar_url = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    google_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())