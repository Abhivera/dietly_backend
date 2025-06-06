# app/services/analytics_service.py
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from app.models.analytics import Analytics
from app.models.meal import Meal, MealItem
from app.models.exercise import UserExercise
from app.models.food import FoodItem
from app.models.exercise import ExerciseItem

class AnalyticsService:
    @staticmethod
    def calculate_daily_analytics(db: Session, user_id: UUID, target_date: date) -> Analytics:
        """Calculate daily analytics for a user"""
        # Calculate total calories consumed
        total_calories_in = db.query(
            func.sum(FoodItem.calories * MealItem.quantity)
        ).join(MealItem).join(Meal).filter(
            Meal.user_id == user_id,
            Meal.meal_date == target_date
        ).scalar() or 0
        
        # Calculate total calories burned through exercises
        total_calories_out = db.query(
            func.sum(ExerciseItem.calories_burnt * UserExercise.duration_mins / ExerciseItem.duration_mins)
        ).join(UserExercise).filter(
            UserExercise.user_id == user_id,
            func.date(UserExercise.date) == target_date
        ).scalar() or 0
        
        # Calculate net calories
        net_calories = int(total_calories_in) - int(total_calories_out)
        
        # Check if analytics already exists for this date
        existing_analytics = db.query(Analytics).filter(
            Analytics.user_id == user_id,
            Analytics.date == target_date
        ).first()
        
        if existing_analytics:
            # Update existing record
            existing_analytics.total_calories_in = int(total_calories_in)
            existing_analytics.total_calories_out = int(total_calories_out)
            existing_analytics.net_calories = net_calories
            db.commit()
            return existing_analytics
        else:
            # Create new record
            analytics = Analytics(
                user_id=user_id,
                date=target_date,
                total_calories_in=int(total_calories_in),
                total_calories_out=int(total_calories_out),
                net_calories=net_calories
            )
            db.add(analytics)
            db.commit()
            db.refresh(analytics)
            return analytics
    
    @staticmethod
    def update_user_analytics(db: Session, user_id: UUID, days_back: int = 7) -> None:
        """Update analytics for the last N days for a user"""
        for i in range(days_back):
            target_date = date.today() - timedelta(days=i)
            AnalyticsService.calculate_daily_analytics(db, user_id, target_date)
    
    @staticmethod
    def get_weekly_summary(db: Session, user_id: UUID) -> dict:
        """Get weekly analytics summary"""
        start_date = date.today() - timedelta(days=7)
        
        analytics = db.query(Analytics).filter(
            Analytics.user_id == user_id,
            Analytics.date >= start_date
        ).all()
        
        if not analytics:
            return {
                "total_days": 0,
                "avg_calories_in": 0,
                "avg_calories_out": 0,
                "avg_net_calories": 0,
                "total_calories_in": 0,
                "total_calories_out": 0
            }
        
        total_calories_in = sum(a.total_calories_in for a in analytics)
        total_calories_out = sum(a.total_calories_out for a in analytics)
        total_days = len(analytics)
        
        return {
            "total_days": total_days,
            "avg_calories_in": total_calories_in / total_days,
            "avg_calories_out": total_calories_out / total_days,
            "avg_net_calories": (total_calories_in - total_calories_out) / total_days,
            "total_calories_in": total_calories_in,
            "total_calories_out": total_calories_out
        }
