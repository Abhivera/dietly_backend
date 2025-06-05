from sqlalchemy import Column, String, Date, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum

class RecommendationType(enum.Enum):
    FOOD = "Food"
    EXERCISE = "Exercise"

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(Enum(RecommendationType), nullable=False)
    recommended_item_id = Column(UUID(as_uuid=True), nullable=False)  # Polymorphic
    date = Column(Date, nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="recommendations")