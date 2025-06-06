from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import user, food, exercise, meal, analytics, recommendation, vlog
from app.models.user import User, UserRole
from app.models.food import FoodItem
from app.models.exercise import ExerciseItem
from app.core.security import get_password_hash

def init_db():
    """Initialize database with base data"""
    # Create all tables
    user.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Create admin user if doesn't exist
        admin_user = db.query(User).filter(User.email == "admin@fitnesstracker.com").first()
        if not admin_user:
            admin_user = User(
                name="Admin User",
                email="admin@fitnesstracker.com",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
        
        # Add predefined food items
        predefined_foods = [
            {"name": "Apple", "calories": 95},
            {"name": "Banana", "calories": 105},
            {"name": "Orange", "calories": 85},
            {"name": "Chicken Breast (100g)", "calories": 165},
            {"name": "Rice (1 cup cooked)", "calories": 205},
            {"name": "Bread (1 slice)", "calories": 80},
            {"name": "Egg (1 large)", "calories": 70},
            {"name": "Milk (1 cup)", "calories": 150},
            {"name": "Yogurt (1 cup)", "calories": 150},
            {"name": "Oatmeal (1 cup)", "calories": 150}
        ]
        
        for food_data in predefined_foods:
            existing_food = db.query(FoodItem).filter(FoodItem.name == food_data["name"]).first()
            if not existing_food:
                food_item = FoodItem(
                    name=food_data["name"],
                    calories=food_data["calories"],
                    is_predefined=True
                )
                db.add(food_item)
        
        # Add predefined exercises
        predefined_exercises = [
            {"name": "Running", "duration_mins": 30, "calories_burnt": 300},
            {"name": "Walking", "duration_mins": 30, "calories_burnt": 150},
            {"name": "Cycling", "duration_mins": 30, "calories_burnt": 250},
            {"name": "Swimming", "duration_mins": 30, "calories_burnt": 350},
            {"name": "Push-ups", "duration_mins": 15, "calories_burnt": 100},
            {"name": "Sit-ups", "duration_mins": 15, "calories_burnt": 80},
            {"name": "Yoga", "duration_mins": 45, "calories_burnt": 200},
            {"name": "Weight Training", "duration_mins": 45, "calories_burnt": 300},
            {"name": "Jump Rope", "duration_mins": 15, "calories_burnt": 200},
            {"name": "Burpees", "duration_mins": 10, "calories_burnt": 150}
        ]
        
        for exercise_data in predefined_exercises:
            existing_exercise = db.query(ExerciseItem).filter(ExerciseItem.name == exercise_data["name"]).first()
            if not existing_exercise:
                exercise_item = ExerciseItem(
                    name=exercise_data["name"],
                    duration_mins=exercise_data["duration_mins"],
                    calories_burnt=exercise_data["calories_burnt"],
                    is_predefined=True
                )
                db.add(exercise_item)
        
        db.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()