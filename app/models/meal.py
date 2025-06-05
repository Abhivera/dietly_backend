from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Meal(Base):
    __tablename__ = "meals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    meal_date = Column(Date, nullable=False)
    meal_time = Column(Time, nullable=False)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="meals")

class MealItem(Base):
    __tablename__ = "meal_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meal_id = Column(UUID(as_uuid=True), ForeignKey("meals.id"), nullable=False)
    food_item_id = Column(UUID(as_uuid=True), ForeignKey("food_items.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    
    # Relationships
    meal = relationship("Meal", backref="meal_items")
    food_item = relationship("FoodItem", backref="meal_items")