from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class UserCalories(Base):
    __tablename__ = "user_calories"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    activity_date = Column(Date, nullable=False, index=True)
    calories_burn = Column(Integer, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="user_calories")
    
    def __repr__(self):
        return f"<UserCalories(id={self.id}, user_id={self.user_id}, activity_date='{self.activity_date}', calories_burn={self.calories_burn})>" 