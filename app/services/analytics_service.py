from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from datetime import datetime, timedelta
from app.models.user import User
from app.models.meal import Meal, MealType
from app.models.workout import Workout
from app.models.daily_log import DailyLog
from app.models.food import Food
from app.models.exercise import Exercise
import statistics

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_nutrition_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive nutrition analytics for the user"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Get meals within the date range
        meals = self.db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.date >= start_date
        ).all()
        
        if not meals:
            return {"message": "No meal data found for the specified period"}
        
        # Calculate daily nutrition totals
        daily_nutrition = {}
        for meal in meals:
            date_str = meal.date.strftime('%Y-%m-%d')
            if date_str not in daily_nutrition:
                daily_nutrition[date_str] = {
                    'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'fiber': 0,
                    'meals_count': 0, 'date': meal.date
                }
            
            # Calculate nutrition based on portion size
            portion_factor = meal.portion_size / 100  # assuming food nutrition is per 100g
            
            if meal.food:
                daily_nutrition[date_str]['calories'] += (meal.food.calories_per_100g or 0) * portion_factor
                daily_nutrition[date_str]['protein'] += (meal.food.protein or 0) * portion_factor
                daily_nutrition[date_str]['carbs'] += (meal.food.carbs or 0) * portion_factor
                daily_nutrition[date_str]['fat'] += (meal.food.fat or 0) * portion_factor
                daily_nutrition[date_str]['fiber'] += (meal.food.fiber or 0) * portion_factor
            
            daily_nutrition[date_str]['meals_count'] += 1
        
        # Calculate statistics
        daily_values = list(daily_nutrition.values())
        
        avg_calories = statistics.mean([day['calories'] for day in daily_values])
        avg_protein = statistics.mean([day['protein'] for day in daily_values])
        avg_carbs = statistics.mean([day['carbs'] for day in daily_values])
        avg_fat = statistics.mean([day['fat'] for day in daily_values])
        avg_fiber = statistics.mean([day['fiber'] for day in daily_values])
        
        # Meal type distribution
        meal_type_counts = {}
        for meal in meals:
            meal_type = meal.meal_type.value if meal.meal_type else 'unknown'
            meal_type_counts[meal_type] = meal_type_counts.get(meal_type, 0) + 1
        
        # Top foods consumed
        food_consumption = {}
        for meal in meals:
            if meal.food:
                food_name = meal.food.name
                if food_name not in food_consumption:
                    food_consumption[food_name] = {'count': 0, 'total_portion': 0}
                food_consumption[food_name]['count'] += 1
                food_consumption[food_name]['total_portion'] += meal.portion_size
        
        top_foods = sorted(
            food_consumption.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:10]
        
        return {
            "period_days": days,
            "total_meals_logged": len(meals),
            "daily_averages": {
                "calories": round(avg_calories, 2),
                "protein": round(avg_protein, 2),
                "carbs": round(avg_carbs, 2),
                "fat": round(avg_fat, 2),
                "fiber": round(avg_fiber, 2)
            },
            "meal_type_distribution": meal_type_counts,
            "top_foods": [
                {
                    "name": food[0],
                    "consumption_count": food[1]['count'],
                    "total_portion_g": round(food[1]['total_portion'], 2)
                }
                for food in top_foods
            ],
            "daily_nutrition_timeline": [
                {
                    "date": date,
                    "calories": round(data['calories'], 2),
                    "protein": round(data['protein'], 2),
                    "carbs": round(data['carbs'], 2),
                    "fat": round(data['fat'], 2),
                    "fiber": round(data['fiber'], 2),
                    "meals_count": data['meals_count']
                }
                for date, data in sorted(daily_nutrition.items())
            ]
        }
    
    def get_fitness_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive fitness analytics for the user"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Get workouts within the date range
        workouts = self.db.query(Workout).filter(
            Workout.user_id == user_id,
            Workout.date >= start_date
        ).all()
        
        if not workouts:
            return {"message": "No workout data found for the specified period"}
        
        # Calculate daily workout totals
        daily_workouts = {}
        for workout in workouts:
            date_str = workout.date.strftime('%Y-%m-%d')
            if date_str not in daily_workouts:
                daily_workouts[date_str] = {
                    'total_duration': 0, 'total_calories': 0, 'workout_count': 0,
                    'exercises': set(), 'date': workout.date
                }
            
            daily_workouts[date_str]['total_duration'] += workout.duration_minutes or 0
            daily_workouts[date_str]['total_calories'] += workout.calories_burned or 0
            daily_workouts[date_str]['workout_count'] += 1
            
            if workout.exercise:
                daily_workouts[date_str]['exercises'].add(workout.exercise.name)
        
        # Calculate statistics
        daily_values = list(daily_workouts.values())
        
        total_workouts = len(workouts)
        total_duration = sum(workout.duration_minutes or 0 for workout in workouts)
        total_calories_burned = sum(workout.calories_burned or 0 for workout in workouts)
        
        avg_duration = statistics.mean([day['total_duration'] for day in daily_values if day['total_duration'] > 0])
        avg_calories = statistics.mean([day['total_calories'] for day in daily_values if day['total_calories'] > 0])
        
        # Exercise frequency
        exercise_frequency = {}
        for workout in workouts:
            if workout.exercise:
                exercise_name = workout.exercise.name
                exercise_frequency[exercise_name] = exercise_frequency.get(exercise_name, 0) + 1
        
        top_exercises = sorted(
            exercise_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Workout consistency (days with workouts)
        workout_days = len([day for day in daily_values if day['workout_count'] > 0])
        consistency_percentage = (workout_days / days) * 100
        
        return {
            "period_days": days,
            "total_workouts": total_workouts,
            "total_duration_minutes": total_duration,
            "total_calories_burned": total_calories_burned,
            "workout_days": workout_days,
            "consistency_percentage": round(consistency_percentage, 2),
            "averages": {
                "duration_per_workout": round(avg_duration, 2) if daily_values else 0,
                "calories_per_workout": round(avg_calories, 2) if daily_values else 0,
                "workouts_per_week": round((total_workouts / days) * 7, 2)
            },
            "top_exercises": [
                {
                    "name": exercise[0],
                    "frequency": exercise[1]
                }
                for exercise in top_exercises
            ],
            "daily_workout_timeline": [
                {
                    "date": date,
                    "total_duration": data['total_duration'],
                    "total_calories": data['total_calories'],
                    "workout_count": data['workout_count'],
                    "unique_exercises": len(data['exercises'])
                }
                for date, data in sorted(daily_workouts.items())
            ]
        }
    
    def get_progress_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get progress analytics combining nutrition and fitness data"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Get daily logs
        daily_logs = self.db.query(DailyLog).filter(
            DailyLog.user_id == user_id,
            DailyLog.date >= start_date
        ).order_by(DailyLog.date).all()
        
        if not daily_logs:
            return {"message": "No daily log data found for the specified period"}
        
        # Weight progress
        weight_data = [
            {"date": log.date.strftime('%Y-%m-%d'), "weight": float(log.weight)}
            for log in daily_logs if log.weight
        ]
        
        # Calculate weight change