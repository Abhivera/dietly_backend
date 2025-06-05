from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from app.models.user import User, Gender
from app.models.food import Food, FoodCategory
from app.models.exercise import Exercise, ExerciseType
from app.models.meal import Meal, MealType
from app.models.workout import Workout
from app.models.daily_log import DailyLog
import random

class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_food_recommendations(self, user_id: str, meal_type: MealType, limit: int = 10) -> List[Dict[str, Any]]:
        """Get personalized food recommendations based on user's dietary history and preferences"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # Get user's recent meal history
        recent_meals = self.db.query(Meal).filter(
            Meal.user_id == user_id,
            Meal.date >= datetime.now() - timedelta(days=30)
        ).all()
        
        # Get frequently consumed foods
        consumed_food_ids = [meal.food_id for meal in recent_meals if meal.food_id]
        
        # Calculate user's average daily calorie needs
        daily_calorie_need = self._calculate_daily_calorie_need(user)
        meal_calorie_target = self._get_meal_calorie_target(meal_type, daily_calorie_need)
        
        # Get foods suitable for the meal type and calorie range
        recommended_foods = self.db.query(Food).filter(
            Food.calories_per_100g.between(
                meal_calorie_target * 0.1,  # Min calories
                meal_calorie_target * 2.0   # Max calories
            )
        ).limit(limit * 2).all()  # Get more to filter later
        
        # Score foods based on various factors
        scored_foods = []
        for food in recommended_foods:
            score = self._calculate_food_score(
                food, user, consumed_food_ids, meal_type, meal_calorie_target
            )
            scored_foods.append({
                "food": food,
                "score": score,
                "reason": self._get_recommendation_reason(food, meal_type, score)
            })
        
        # Sort by score and return top recommendations
        scored_foods.sort(key=lambda x: x["score"], reverse=True)
        
        return [{
            "id": item["food"].id,
            "name": item["food"].name,
            "category": item["food"].category.value if item["food"].category else None,
            "calories_per_100g": item["food"].calories_per_100g,
            "protein": item["food"].protein,
            "carbs": item["food"].carbs,
            "fat": item["food"].fat,
            "fiber": item["food"].fiber,
            "score": item["score"],
            "reason": item["reason"]
        } for item in scored_foods[:limit]]
    
    def get_exercise_recommendations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get personalized exercise recommendations based on user's fitness level and history"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # Get user's recent workout history
        recent_workouts = self.db.query(Workout).filter(
            Workout.user_id == user_id,
            Workout.date >= datetime.now() - timedelta(days=30)
        ).all()
        
        # Get frequently performed exercises
        performed_exercise_ids = [workout.exercise_id for workout in recent_workouts if workout.exercise_id]
        
        # Calculate user's fitness level based on recent activity
        fitness_level = self._calculate_fitness_level(recent_workouts)
        
        # Get suitable exercises
        recommended_exercises = self.db.query(Exercise).filter(
            Exercise.difficulty_level <= fitness_level + 1  # Allow slightly challenging exercises
        ).limit(limit * 2).all()
        
        # Score exercises based on various factors
        scored_exercises = []
        for exercise in recommended_exercises:
            score = self._calculate_exercise_score(
                exercise, user, performed_exercise_ids, fitness_level
            )
            scored_exercises.append({
                "exercise": exercise,
                "score": score,
                "reason": self._get_exercise_recommendation_reason(exercise, fitness_level, score)
            })
        
        # Sort by score and return top recommendations
        scored_exercises.sort(key=lambda x: x["score"], reverse=True)
        
        return [{
            "id": item["exercise"].id,
            "name": item["exercise"].name,
            "type": item["exercise"].type.value if item["exercise"].type else None,
            "difficulty_level": item["exercise"].difficulty_level,
            "calories_per_minute": item["exercise"].calories_per_minute,
            "muscle_groups": item["exercise"].muscle_groups,
            "equipment_needed": item["exercise"].equipment_needed,
            "score": item["score"],
            "reason": item["reason"]
        } for item in scored_exercises[:limit]]
    
    def get_meal_plan_recommendations(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Generate a meal plan for the specified number of days"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        daily_calorie_need = self._calculate_daily_calorie_need(user)
        meal_plan = {}
        
        for day in range(days):
            date = datetime.now() + timedelta(days=day)
            day_name = date.strftime("%A")
            
            # Get recommendations for each meal type
            breakfast = self.get_food_recommendations(user_id, MealType.BREAKFAST, limit=3)
            lunch = self.get_food_recommendations(user_id, MealType.LUNCH, limit=3)
            dinner = self.get_food_recommendations(user_id, MealType.DINNER, limit=3)
            snacks = self.get_food_recommendations(user_id, MealType.SNACK, limit=2)
            
            meal_plan[day_name] = {
                "date": date.strftime("%Y-%m-%d"),
                "breakfast": breakfast[:1] if breakfast else [],
                "lunch": lunch[:1] if lunch else [],
                "dinner": dinner[:1] if dinner else [],
                "snacks": snacks[:1] if snacks else [],
                "total_target_calories": daily_calorie_need
            }
        
        return meal_plan
    
    def get_workout_recommendations(self, user_id: str, duration_minutes: int = 30) -> Dict[str, Any]:
        """Generate a workout plan for the specified duration"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Get exercise recommendations
        exercises = self.get_exercise_recommendations(user_id, limit=20)
        
        # Create a balanced workout
        cardio_exercises = [e for e in exercises if e.get("type") == ExerciseType.CARDIO.value]
        strength_exercises = [e for e in exercises if e.get("type") == ExerciseType.STRENGTH.value]
        flexibility_exercises = [e for e in exercises if e.get("type") == ExerciseType.FLEXIBILITY.value]
        
        # Distribute time across exercise types
        cardio_time = duration_minutes * 0.4
        strength_time = duration_minutes * 0.4
        flexibility_time = duration_minutes * 0.2
        
        workout_plan = {
            "total_duration_minutes": duration_minutes,
            "warm_up": {
                "duration_minutes": 5,
                "exercises": flexibility_exercises[:2] if flexibility_exercises else []
            },
            "cardio": {
                "duration_minutes": int(cardio_time),
                "exercises": cardio_exercises[:2] if cardio_exercises else []
            },
            "strength": {
                "duration_minutes": int(strength_time),
                "exercises": strength_exercises[:3] if strength_exercises else []
            },
            "cool_down": {
                "duration_minutes": 5,
                "exercises": flexibility_exercises[2:4] if len(flexibility_exercises) > 2 else []
            }
        }
        
        return workout_plan
    
    def _calculate_daily_calorie_need(self, user: User) -> int:
        """Calculate daily calorie needs using Mifflin-St Jeor equation"""
        if not user.age:
            return 2000  # Default value
        
        # Assuming average weight and height if not provided
        weight = 70  # kg (default)
        height = 170  # cm (default)
        
        # Base Metabolic Rate (BMR)
        if user.gender == Gender.MALE:
            bmr = 10 * weight + 6.25 * height - 5 * user.age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * user.age - 161
        
        # Apply activity factor (assuming moderate activity)
        activity_factor = 1.55
        return int(bmr * activity_factor)
    
    def _get_meal_calorie_target(self, meal_type: MealType, daily_calories: int) -> int:
        """Get target calories for a specific meal type"""
        if meal_type == MealType.BREAKFAST:
            return int(daily_calories * 0.25)
        elif meal_type == MealType.LUNCH:
            return int(daily_calories * 0.35)
        elif meal_type == MealType.DINNER:
            return int(daily_calories * 0.30)
        else:  # SNACK
            return int(daily_calories * 0.10)
    
    def _calculate_food_score(self, food: Food, user: User, consumed_food_ids: List[str], 
                            meal_type: MealType, target_calories: int) -> float:
        """Calculate recommendation score for a food item"""
        score = 0.0
        
        # Nutritional balance score
        if food.protein and food.carbs and food.fat:
            # Prefer balanced macros
            total_macros = food.protein + food.carbs + food.fat
            if total_macros > 0:
                protein_ratio = food.protein / total_macros
                if 0.15 <= protein_ratio <= 0.35:  # Good protein ratio
                    score += 30
        
        # Calorie appropriateness
        calorie_diff = abs(food.calories_per_100g - target_calories)
        if calorie_diff < target_calories * 0.2:
            score += 25
        
        # Fiber content (higher is better)
        if food.fiber:
            score += min(food.fiber * 2, 20)
        
        # Novelty (prefer foods not eaten recently)
        if food.id not in consumed_food_ids:
            score += 15
        
        # Meal type appropriateness
        if meal_type == MealType.BREAKFAST and food.category in [FoodCategory.GRAINS, FoodCategory.FRUITS]:
            score += 10
        elif meal_type == MealType.LUNCH and food.category in [FoodCategory.PROTEINS, FoodCategory.VEGETABLES]:
            score += 10
        elif meal_type == MealType.DINNER and food.category in [FoodCategory.PROTEINS, FoodCategory.VEGETABLES]:
            score += 10
        
        return score
    
    def _calculate_fitness_level(self, recent_workouts: List[Workout]) -> int:
        """Calculate user's fitness level based on recent workouts"""
        if not recent_workouts:
            return 1  # Beginner
        
        avg_duration = sum(w.duration_minutes for w in recent_workouts) / len(recent_workouts)
        workout_frequency = len(recent_workouts) / 4  # per week over last month
        
        if avg_duration >= 45 and workout_frequency >= 4:
            return 3  # Advanced
        elif avg_duration >= 30 and workout_frequency >= 3:
            return 2  # Intermediate
        else:
            return 1  # Beginner
    
    def _calculate_exercise_score(self, exercise: Exercise, user: User, 
                                performed_exercise_ids: List[str], fitness_level: int) -> float:
        """Calculate recommendation score for an exercise"""
        score = 0.0
        
        # Difficulty appropriateness
        if exercise.difficulty_level == fitness_level:
            score += 30
        elif abs(exercise.difficulty_level - fitness_level) == 1:
            score += 20
        
        # Calorie burn potential
        if exercise.calories_per_minute:
            score += min(exercise.calories_per_minute * 2, 25)
        
        # Novelty (prefer exercises not done recently)
        if exercise.id not in performed_exercise_ids:
            score += 20
        
        # Equipment availability (prefer bodyweight exercises)
        if not exercise.equipment_needed or exercise.equipment_needed == "None":
            score += 15
        
        # Muscle group variety
        if exercise.muscle_groups and len(exercise.muscle_groups.split(',')) > 1:
            score += 10
        
        return score
    
    def _get_recommendation_reason(self, food: Food, meal_type: MealType, score: float) -> str:
        """Generate a human-readable reason for food recommendation"""
        reasons = []
        
        if food.fiber and food.fiber > 3:
            reasons.append("high fiber content")
        
        if food.protein and food.protein > 10:
            reasons.append("good protein source")
        
        if meal_type == MealType.BREAKFAST and food.category == FoodCategory.FRUITS:
            reasons.append("great for breakfast energy")
        
        if not reasons:
            reasons.append("well-balanced nutrition")
        
        return f"Recommended for {', '.join(reasons)}"
    
    def _get_exercise_recommendation_reason(self, exercise: Exercise, fitness_level: int, score: float) -> str:
        """Generate a human-readable reason for exercise recommendation"""
        reasons = []
        
        if exercise.difficulty_level == fitness_level:
            reasons.append("matches your fitness level")
        
        if exercise.calories_per_minute and exercise.calories_per_minute > 8:
            reasons.append("high calorie burn")
        
        if not exercise.equipment_needed or exercise.equipment_needed == "None":
            reasons.append("no equipment needed")
        
        if not reasons:
            reasons.append("well-suited for your goals")
        
        return f"Recommended because it {', '.join(reasons)}"