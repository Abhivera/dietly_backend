from celery import Celery
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.analytics_service import AnalyticsService
from app.services.recommendation_service import RecommendationService
from datetime import date

# Initialize Celery (optional - for background tasks)
celery_app = Celery(
    "fitness_tracker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task
def update_daily_analytics(user_id: str):
    """Background task to update daily analytics for a user"""
    db = SessionLocal()
    try:
        from uuid import UUID
        user_uuid = UUID(user_id)
        AnalyticsService.calculate_daily_analytics(db, user_uuid, date.today())
        RecommendationService.generate_daily_recommendations(db, user_uuid)
    finally:
        db.close()

@celery_app.task
def process_all_users_analytics():
    """Background task to process analytics for all users"""
    db = SessionLocal()
    try:
        from app.models.user import User
        users = db.query(User).filter(User.is_active == True).all()
        
        for user in users:
            AnalyticsService.update_user_analytics(db, user.id, days_back=1)
            RecommendationService.generate_daily_recommendations(db, user.id)
    finally:
        db.close()