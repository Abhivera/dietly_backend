#!/usr/bin/env python3
"""
Example usage of the updated UserCalories PUT endpoint
"""

import requests
import json
from datetime import date

# Example API base URL (adjust as needed)
BASE_URL = "http://localhost:8000/api/v1"

def example_put_request():
    """Example of how to use the PUT endpoint"""
    
    # Example 1: Update with new activities
    print("=== Example 1: Update with new activities ===")
    
    update_data_1 = {
        "activity_date": "2024-01-15",
        "calories_burned": [
            {
                "activity_name": "running",
                "calories": "250"
            },
            {
                "activity_name": "cycling",
                "calories": "180"
            },
            {
                "activity_name": "swimming",
                "calories": "200"
            }
        ]
    }
    
    print("Request Body:")
    print(json.dumps(update_data_1, indent=2))
    
    # Example API call (commented out as it requires authentication)
    # response = requests.put(
    #     f"{BASE_URL}/user-calories/123",
    #     json=update_data_1,
    #     headers={"Authorization": "Bearer your_token_here"}
    # )
    # print(f"Response Status: {response.status_code}")
    # print(f"Response Body: {response.json()}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 2: Partial update (only calories_burned)
    print("=== Example 2: Partial update (only calories_burned) ===")
    
    update_data_2 = {
        "calories_burned": [
            {
                "activity_name": "yoga",
                "calories": "150"
            },
            {
                "activity_name": "walking",
                "calories": "100"
            }
        ]
    }
    
    print("Request Body:")
    print(json.dumps(update_data_2, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Example 3: Update only the date
    print("=== Example 3: Update only the date ===")
    
    update_data_3 = {
        "activity_date": "2024-01-16"
    }
    
    print("Request Body:")
    print(json.dumps(update_data_3, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Example 4: Invalid data examples
    print("=== Example 4: Invalid data examples ===")
    
    # Invalid: Duplicate activity names
    invalid_data_1 = {
        "calories_burned": [
            {
                "activity_name": "running",
                "calories": "250"
            },
            {
                "activity_name": "running",  # Duplicate!
                "calories": "200"
            }
        ]
    }
    print("Invalid: Duplicate activity names")
    print(json.dumps(invalid_data_1, indent=2))
    
    print("\n---")
    
    # Invalid: Negative calories
    invalid_data_2 = {
        "calories_burned": [
            {
                "activity_name": "running",
                "calories": "-50"  # Negative!
            }
        ]
    }
    print("Invalid: Negative calories")
    print(json.dumps(invalid_data_2, indent=2))
    
    print("\n---")
    
    # Invalid: Empty activity name
    invalid_data_3 = {
        "calories_burned": [
            {
                "activity_name": "",  # Empty!
                "calories": "100"
            }
        ]
    }
    print("Invalid: Empty activity name")
    print(json.dumps(invalid_data_3, indent=2))
    
    print("\n---")
    
    # Invalid: Future date
    invalid_data_4 = {
        "activity_date": "2025-12-31",  # Future date!
        "calories_burned": [
            {
                "activity_name": "running",
                "calories": "250"
            }
        ]
    }
    print("Invalid: Future date")
    print(json.dumps(invalid_data_4, indent=2))

def curl_examples():
    """Example curl commands"""
    print("\n" + "="*50)
    print("=== CURL Examples ===")
    print("="*50)
    
    print("\n1. Update with new activities:")
    print("""
curl -X PUT "http://localhost:8000/api/v1/user-calories/123" \\
  -H "Authorization: Bearer your_token_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "activity_date": "2024-01-15",
    "calories_burned": [
      {
        "activity_name": "running",
        "calories": "250"
      },
      {
        "activity_name": "cycling",
        "calories": "180"
      }
    ]
  }'
""")
    
    print("\n2. Partial update (only activities):")
    print("""
curl -X PUT "http://localhost:8000/api/v1/user-calories/123" \\
  -H "Authorization: Bearer your_token_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "calories_burned": [
      {
        "activity_name": "swimming",
        "calories": "300"
      }
    ]
  }'
""")
    
    print("\n3. Update only the date:")
    print("""
curl -X PUT "http://localhost:8000/api/v1/user-calories/123" \\
  -H "Authorization: Bearer your_token_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "activity_date": "2024-01-16"
  }'
""")

def validation_rules_summary():
    """Summary of validation rules"""
    print("\n" + "="*50)
    print("=== Validation Rules Summary ===")
    print("="*50)
    
    rules = [
        "Activity names cannot be empty or exceed 100 characters",
        "Calories must be valid numbers between 0 and 10,000",
        "No duplicate activity names allowed (case insensitive)",
        "Total daily calories cannot exceed 5,000",
        "Activity date cannot be in the future",
        "At least one activity must be provided",
        "All fields are optional in updates (partial updates supported)"
    ]
    
    for i, rule in enumerate(rules, 1):
        print(f"{i}. {rule}")

if __name__ == "__main__":
    example_put_request()
    curl_examples()
    validation_rules_summary() 