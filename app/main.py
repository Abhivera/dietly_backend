from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, users, images
from app.core.config import settings

app = FastAPI(
    title="FastAPI Image Analysis App",
    description="A production-ready FastAPI application with user authentication and image analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 👈 your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(images.router, prefix="/api/v1/images", tags=["images"])

@app.get("/")
def read_root():
    return {"message": "FastAPI Image Analysis App is running!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}