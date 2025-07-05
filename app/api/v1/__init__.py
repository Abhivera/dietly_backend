from fastapi import APIRouter
from . import auth, users, images, meal, public_food_analysis

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(meal.router, prefix="/meal", tags=["meal"])
api_router.include_router(public_food_analysis.router, prefix="/public", tags=["public-food-analysis"])