from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import os

from app.core.config import settings
from app.api.v1 import auth,users,foods,exercises,meals,analytics,recommendations,vlogs # Uncomment others as needed

from app.core.database import get_db

  # Make sure you have get_db defined in this module


# Create uploads directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


# Health check endpoints
@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/health/detailed")
def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check including database connectivity"""
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "database": db_status,
        "environment": "production" if not settings.DEBUG else "development"
    }


# Metrics endpoint
@app.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    """Basic metrics endpoint"""
    from app.models.user import User
    from app.models.meal import Meal
    from app.models.vlog import Vlog

    total_users = db.query(User).count()
    total_meals = db.query(Meal).count()
    total_vlogs = db.query(Vlog).count()
    active_users = db.query(User).filter(User.is_active == True).count()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_meals": total_meals,
        "total_vlogs": total_vlogs,
        "timestamp": datetime.utcnow().isoformat()
    }


# Default root endpoint
@app.get("/")
def root():
    return {"message": f"Welcome to {settings.APP_NAME} v{settings.VERSION}"}


# Register routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(foods.router, prefix="/api/v1/foods", tags=["Foods"])
app.include_router(exercises.router, prefix="/api/v1/exercises", tags=["Exercises"])
app.include_router(meals.router, prefix="/api/v1/meals", tags=["Meals"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recommendations"])
app.include_router(vlogs.router, prefix="/api/v1/vlogs", tags=["Vlogs"])
