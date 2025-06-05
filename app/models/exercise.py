from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class ExerciseItem(Base):
    __tablename__ = "exercise_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    duration_mins = Column(Integer, nullable=False)
    calories_burnt = Column(Integer, nullable=False)
    is_predefined = Column(Boolean, default=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="exercise_items")

class UserExercise(Base):
    __tablename__ = "user_exercises"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    exercise_item_id = Column(UUID(as_uuid=True), ForeignKey("exercise_items.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    duration_mins = Column(Integer, nullable=False)
    
    # Relationships
    user = relationship("User", backref="user_exercises")
    exercise_item = relationship("ExerciseItem", backref="user_exercises")