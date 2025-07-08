from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, users, images, meal, public_food_analysis
from app.core.config import settings
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(
    title="FastAPI Image Analysis App",
    description="A production-ready FastAPI application with user authentication and image analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=['https://dietly.org'],  # Only allow your frontend
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