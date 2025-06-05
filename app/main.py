from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth 
#, users, foods, exercises, meals, analytics, recommendations, vlogs

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
# app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
# app.include_router(foods.router, prefix="/api/v1/foods", tags=["Foods"])
# app.include_router(exercises.router, prefix="/api/v1/exercises", tags=["Exercises"])
# app.include_router(meals.router, prefix="/api/v1/meals", tags=["Meals"])
# app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
# app.include_router(recommendations.router, prefix="/api/v1/recommendations", tags=["Recommendations"])
# app.include_router(vlogs.router, prefix="/api/v1/vlogs", tags=["Vlogs"])

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.APP_NAME} v{settings.VERSION}"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}