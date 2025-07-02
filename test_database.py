# quick_fix_check.py
# Quick script to identify the most common "200 but no user saved" issues

import os
import sys
from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

def check_common_issues():
    """Check the most common issues that cause 200 response but no user saved"""
    

    issues_found = []
    fixes = []
    
    # 1. Check if database URL is correct
    print("\n1. 📊 Checking Database Connection...")
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("   ✅ Database connection OK")
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        issues_found.append("Database connection failed")
        fixes.append("Check DATABASE_URL in .env file")
    
 
  
    
 
    
  
if __name__ == "__main__":
    check_common_issues()