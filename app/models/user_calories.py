from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class UserCalories(Base):
    __tablename__ = "user_calories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    activity_date = Column(Date, nullable=False, index=True)
    calories_burned = Column(JSON, nullable=False)  # Store as JSON array
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Unique constraint activity_date combination
    __table_args__ = (
        UniqueConstraint('activity_date', name='uq_user_activity_date'),
    )
    
    # Relationship
    user = relationship("User", back_populates="user_calories")
    
    def __repr__(self):
        return f"<UserCalories(id={self.id}, user_id={self.user_id}, activity_date='{self.activity_date}', calories_burned={self.calories_burned})>"