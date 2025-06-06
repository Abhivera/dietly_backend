from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date, timedelta
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.analytics import Analytics
from app.schemas.analytics import AnalyticsResponse, AnalyticsSummary

router = APIRouter()

@router.get("/{user_id}", response_model=List[AnalyticsResponse])
def get_user_analytics(
    user_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this data")
    
    query = db.query(Analytics).filter(Analytics.user_id == user_id)
    
    if start_date:
        query = query.filter(Analytics.date >= start_date)
    if end_date:
        query = query.filter(Analytics.date <= end_date)
    
    analytics = query.order_by(Analytics.date.desc()).all()
    return analytics

@router.get("/{user_id}/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    user_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this data")
    
    start_date = date.today() - timedelta(days=days)
    analytics = db.query(Analytics).filter(
        Analytics.user_id == user_id,
        Analytics.date >= start_date
    ).all()
    
    if not analytics:
        return AnalyticsSummary(
            total_days=0,
            avg_calories_in=0,
            avg_calories_out=0,
            avg_net_calories=0,
            total_calories_in=0,
            total_calories_out=0
        )
    
    total_calories_in = sum(a.total_calories_in for a in analytics)
    total_calories_out = sum(a.total_calories_out for a in analytics)
    total_days = len(analytics)
    
    return AnalyticsSummary(
        total_days=total_days,
        avg_calories_in=total_calories_in / total_days,
        avg_calories_out=total_calories_out / total_days,
        avg_net_calories=(total_calories_in - total_calories_out) / total_days,
        total_calories_in=total_calories_in,
        total_calories_out=total_calories_out
    )