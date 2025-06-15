from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Image(Base):
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Analysis fields
    is_food = Column(Boolean, nullable=True)  # True if image contains food, False if not
    analysis_description = Column(Text, nullable=True)
    food_items = Column(JSON, nullable=True)  # Store as JSON array
    estimated_calories = Column(Integer, nullable=True)
    nutrients = Column(JSON, nullable=True)  # Store as JSON object
    analysis_confidence = Column(Float, nullable=True)
    analysis_completed = Column(DateTime(timezone=True), nullable=True)
    
    # Relationship
    owner = relationship("User", back_populates="images")
    
    def to_dict(self):
        """Convert model to dictionary including analysis data"""
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "description": self.description,
            "tags": self.tags,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "analysis": {
                "is_food": self.is_food,
                "food_items": self.food_items or [],
                "description": self.analysis_description,
                "calories": self.estimated_calories,
                "nutrients": self.nutrients or {},
                "confidence": self.analysis_confidence,
                "completed_at": self.analysis_completed.isoformat() if self.analysis_completed else None
            }
        }