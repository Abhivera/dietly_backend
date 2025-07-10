from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, users, images, meal, public_food_analysis
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.pending_registration import PendingRegistration
from app.core.database import SessionLocal
from app.core.config import settings
import threading, time

app = FastAPI(
    title="FastAPI Image Analysis App",
    description="A production-ready FastAPI application with user authentication and image analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add SessionMiddleware for OAuth support
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(images.router, prefix="/api/v1/images", tags=["images"])
app.include_router(meal.router, prefix="/api/v1/meal", tags=["meal"])
app.include_router(public_food_analysis.router, prefix="/api/v1/public", tags=["public api"])

@app.get("/")
def read_root():
    return {"message": "FastAPI Image Analysis App is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/health/db")
def database_health_check():
    """Check database connection health"""
    try:
        db = SessionLocal()
        # Try a simple query to test connection
        db.execute("SELECT 1")
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

def cleanup_pending_registrations():
    db: Session = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=1)
        db.query(PendingRegistration).filter(PendingRegistration.created_at < cutoff).delete()
        db.commit()
    finally:
        db.close()

def schedule_cleanup():
    while True:
        cleanup_pending_registrations()
        time.sleep(3600)  # Run every hour

@app.on_event("startup")
def start_cleanup_task():
    threading.Thread(target=schedule_cleanup, daemon=True).start()