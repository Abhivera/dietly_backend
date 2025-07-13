#!/usr/bin/env python3
"""
Test script for UserCalories validation rules
"""

from datetime import date, timedelta
from app.schemas.user_calories import UserCaloriesCreate, UserCaloriesUpdate, ActivityCalories
from pydantic import ValidationError

def test_valid_data():
    """Test valid data scenarios"""
    print("=== Testing Valid Data ===")
    
    # Test 1: Basic valid data
    try:
        valid_data = UserCaloriesCreate(
            activity_date=date.today(),
            calories_burned=[
                ActivityCalories(activity_name="running", calories="250"),
                ActivityCalories(activity_name="cycling", calories="180")
            ]
        )
        print("✓ Basic valid data passed")
    except ValidationError as e:
        print(f"✗ Basic valid data failed: {e}")
    
    # Test 2: Single activity
    try:
        single_activity = UserCaloriesCreate(
            activity_date=date.today(),
            calories_burned=[
                ActivityCalories(activity_name="walking", calories="100")
            ]
        )
        print("✓ Single activity passed")
    except ValidationError as e:
        print(f"✗ Single activity failed: {e}")

def test_activity_name_validation():
    """Test activity name validation"""
    print("\n=== Testing Activity Name Validation ===")
    
    # Test 1: Empty activity name
    try:
        UserCaloriesCreate(
            activity_date=date.today(),
            calories_burned=[
                ActivityCalories(activity_name="", calories="100")
            ]
        )
        print("✗ Empty activity name should have failed")
    except ValidationError as e:
        print("✓ Empty activity name correctly rejected")
    
    # Test 2: Very long activity name
    try:
        UserCaloriesCreate(
            activity_date=date.today(),
            calories_burned=[
                ActivityCalories(activity_name="a" * 101, calories="100")
            ]
        )
        print("✗ Long activity name should have failed")
    except ValidationError as e:
        print("✓ Long activity name correctly rejected")
    
    # Test 3: Whitespace-only activity name
    try:
        UserCaloriesCreate(
            activity_date=date.today(),
            calories_burned=[
                ActivityCalories(activity_name="   ", calories="100")
            ]
        )
        print("✗ Whitespace-only activity name should have failed")
    except ValidationError as e:
        print("✓ Whitespace-only activity name correctly rejected")

def test_calories_validation():
    """Test calories validation"""
    print("\n=== Testing Calories Validation ===")
    
    # Test 1: Negative calories
    try:
        UserCaloriesCreate(
            activity_date=date.today(),
            calories_burned=[
                ActivityCalories(activity_name="running", calories="-50")
            ]
        )
        print("✗ Negative calories should have failed")
    except ValidationError as e:
        print("✓ Negative calories correctly rejected")
    
    # Test 2: Non-numeric calories
    try:
        UserCaloriesCreate(
            activity_date=date.today(),
            calories_burned=[
                ActivityCalories(activity_name="running", calories="abc")
            ]
        )
        print("✗ Non-numeric calories should have failed")
    except ValidationError as e:
        print("✓ Non-numeric calories correctly rejected")
    
    # Test 3: Too high calories
    try:
        UserCaloriesCreate(
            activity_date=date.today(),
            calories_burned=[
                ActivityCalories(activity_name="running", calories="15000")
            ]
        )
        print("✗ Too high calories should have failed")
    except ValidationError as e:
        print("✓ Too high calories correctly rejected")
    
    # Test 4: Empty calories
    try:
        UserCaloriesCreate(
            activity_date=date.today(),
            calories_burned=[
                ActivityCalories(activity_name="running", calories="")
            ]
        )
        print("✗ Empty calories should have failed")
    except ValidationError as e:
        print("✓ Empty calories correctly rejected")

def test_duplicate_activities():
    """Test duplicate activity validation"""
    print("\n=== Testing Duplicate Activities ===")
    
    # Test 1: Duplicate activity names (case insensitive)
    try:
        UserCaloriesCreate(
            activity_date=date.today(),
            calories_burned=[
                ActivityCalories(activity_name="running", calories="250"),
                ActivityCalories(activity_name="Running", calories="200")
            ]
        )
        print("✗ Duplicate activities should have failed")
    except ValidationError as e:
        print("✓ Duplicate activities correctly rejected")
    
    # Test 2: Different activity names
    try:
        UserCaloriesCreate(
            activity_date=date.today(),
            calories_burned=[
                ActivityCalories(activity_name="running", calories="250"),
                ActivityCalories(activity_name="cycling", calories="200")
            ]
        )
        print("✓ Different activities passed")
    except ValidationError as e:
        print(f"✗ Different activities failed: {e}")

def test_total_calories_limit():
    """Test total calories limit validation"""
    print("\n=== Testing Total Calories Limit ===")
    
    # Test 1: Total calories exceeding limit
    try:
        UserCaloriesCreate(
            activity_date=date.today(),
            calories_burned=[
                ActivityCalories(activity_name="running", calories="3000"),
                ActivityCalories(activity_name="cycling", calories="2500")
            ]
        )
        print("✗ Total calories limit should have failed")
    except ValidationError as e:
        print("✓ Total calories limit correctly rejected")
    
    # Test 2: Total calories within limit
    try:
        UserCaloriesCreate(
            activity_date=date.today(),
            calories_burned=[
                ActivityCalories(activity_name="running", calories="1000"),
                ActivityCalories(activity_name="cycling", calories="800"),
                ActivityCalories(activity_name="walking", calories="200")
            ]
        )
        print("✓ Total calories within limit passed")
    except ValidationError as e:
        print(f"✗ Total calories within limit failed: {e}")

def test_date_validation():
    """Test date validation"""
    print("\n=== Testing Date Validation ===")
    
    # Test 1: Future date
    future_date = date.today() + timedelta(days=1)
    try:
        UserCaloriesCreate(
            activity_date=future_date,
            calories_burned=[
                ActivityCalories(activity_name="running", calories="250")
            ]
        )
        print("✗ Future date should have failed")
    except ValidationError as e:
        print("✓ Future date correctly rejected")
    
    # Test 2: Past date
    past_date = date.today() - timedelta(days=1)
    try:
        UserCaloriesCreate(
            activity_date=past_date,
            calories_burned=[
                ActivityCalories(activity_name="running", calories="250")
            ]
        )
        print("✓ Past date passed")
    except ValidationError as e:
        print(f"✗ Past date failed: {e}")

def test_update_validation():
    """Test update validation"""
    print("\n=== Testing Update Validation ===")
    
    # Test 1: Partial update with valid data
    try:
        update_data = UserCaloriesUpdate(
            calories_burned=[
                ActivityCalories(activity_name="swimming", calories="300")
            ]
        )
        print("✓ Partial update passed")
    except ValidationError as e:
        print(f"✗ Partial update failed: {e}")
    
    # Test 2: Update with empty activities
    try:
        UserCaloriesUpdate(
            calories_burned=[]
        )
        print("✗ Empty activities should have failed")
    except ValidationError as e:
        print("✓ Empty activities correctly rejected")

def main():
    """Run all validation tests"""
    print("Starting UserCalories validation tests...\n")
    
    test_valid_data()
    test_activity_name_validation()
    test_calories_validation()
    test_duplicate_activities()
    test_total_calories_limit()
    test_date_validation()
    test_update_validation()
    
    print("\n=== Validation Tests Complete ===")

if __name__ == "__main__":
    main() 