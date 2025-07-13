#!/usr/bin/env python3
"""
Test script for the updated UserCalories model
"""

from datetime import date
from app.core.database import SessionLocal
from app.models.user_calories import UserCalories
from app.models.user import User
from app.schemas.user_calories import UserCaloriesCreate, ActivityCalories

def test_user_calories():
    """Test the new UserCalories structure"""
    
    # Create a test entry with the new structure
    activities = [
        ActivityCalories(activity_name="running", calories="250"),
        ActivityCalories(activity_name="cycling", calories="180"),
        ActivityCalories(activity_name="walking", calories="100")
    ]
    
    # Create schema object
    calories_data = UserCaloriesCreate(
        activity_date=date(2024, 1, 15),
        calories_burned=activities
    )
    
    print("Test data created:")
    print(f"Date: {calories_data.activity_date}")
    print("Activities:")
    for activity in calories_data.calories_burned:
        print(f"  - {activity.activity_name}: {activity.calories} calories")
    
    # Test database operations
    db = SessionLocal()
    try:
        # Check if there are any users in the database
        existing_user = db.query(User).first()
        if existing_user:
            user_id = existing_user.id
            print(f"\nUsing existing user with ID: {user_id}")
        else:
            # Create a test user if none exists
            test_user = User(
                email="test@example.com",
                hashed_password="test_password_hash",
                full_name="Test User"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            user_id = test_user.id
            print(f"\nCreated test user with ID: {user_id}")
        
        # Create a new record
        user_calories = UserCalories(
            user_id=user_id,
            activity_date=calories_data.activity_date,
            calories_burned=[
                {"activity_name": "running", "calories": "250"},
                {"activity_name": "cycling", "calories": "180"},
                {"activity_name": "walking", "calories": "100"}
            ]
        )
        
        print("\nAttempting to save to database...")
        db.add(user_calories)
        db.commit()
        db.refresh(user_calories)
        
        print(f"Record saved with ID: {user_calories.id}")
        print(f"Calories burned data: {user_calories.calories_burned}")
        
        # Test retrieving the record
        retrieved = db.query(UserCalories).filter(UserCalories.id == user_calories.id).first()
        if retrieved:
            print(f"\nRetrieved record:")
            print(f"ID: {retrieved.id}")
            print(f"User ID: {retrieved.user_id}")
            print(f"Date: {retrieved.activity_date}")
            print(f"Activities: {retrieved.calories_burned}")
            
            # Calculate total calories
            total_calories = 0
            for activity in retrieved.calories_burned:
                try:
                    total_calories += int(activity.get("calories", 0))
                except (ValueError, TypeError):
                    continue
            
            print(f"Total calories: {total_calories}")
        
        # Clean up - delete the test record
        db.delete(user_calories)
        db.commit()
        print("\nTest record cleaned up successfully")
        
        # Clean up test user if we created one
        if not existing_user:
            db.delete(test_user)
            db.commit()
            print("Test user cleaned up successfully")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_user_calories() 