# quick_fix_check.py
# Quick script to identify the most common "200 but no user saved" issues

import os
import sys
from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

def check_common_issues():
    """Check the most common issues that cause 200 response but no user saved"""
    
    print("🔍 Quick Fix Check for Google OAuth User Creation")
    print("=" * 60)
    
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
    
    # 2. Check if users table exists and has required columns
    print("\n2. 🗃️  Checking Users Table Structure...")
    try:
        engine = create_engine(settings.database_url)
        inspector = inspect(engine)
        
        if 'users' not in inspector.get_table_names():
            print("   ❌ Users table doesn't exist")
            issues_found.append("Users table missing")
            fixes.append("Run: alembic upgrade head")
        else:
            print("   ✅ Users table exists")
            
            # Check required columns
            columns = inspector.get_columns('users')
            column_names = [col['name'] for col in columns]
            
            required_cols = ['email', 'username', 'google_id', 'avatar_url', 'provider', 'hashed_password']
            missing_cols = [col for col in required_cols if col not in column_names]
            
            if missing_cols:
                print(f"   ❌ Missing columns: {missing_cols}")
                issues_found.append(f"Missing columns: {missing_cols}")
                fixes.append("Run the ALTER TABLE commands from the migration")
            else:
                print("   ✅ All required columns present")
            
            # Check if hashed_password is nullable
            hashed_pwd_col = next((col for col in columns if col['name'] == 'hashed_password'), None)
            if hashed_pwd_col and not hashed_pwd_col['nullable']:
                print("   ❌ hashed_password column is NOT NULL (should be nullable for Google users)")
                issues_found.append("hashed_password not nullable")
                fixes.append("ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;")
            else:
                print("   ✅ hashed_password is nullable")
                
    except Exception as e:
        print(f"   ❌ Error checking table structure: {e}")
        issues_found.append("Table structure check failed")
        fixes.append("Check database schema and run migrations")
    
    # 3. Check Google OAuth configuration
    print("\n3. 🔑 Checking Google OAuth Configuration...")
    config_ok = True
    
    if not settings.google_client_id:
        print("   ❌ GOOGLE_CLIENT_ID not set")
        config_ok = False
    else:
        print(f"   ✅ GOOGLE_CLIENT_ID: {settings.google_client_id[:10]}...")
    
    if not settings.google_client_secret:
        print("   ❌ GOOGLE_CLIENT_SECRET not set")
        config_ok = False
    else:
        print(f"   ✅ GOOGLE_CLIENT_SECRET: {settings.google_client_secret[:5]}...")
    
    print(f"   ✅ GOOGLE_REDIRECT_URI: {settings.google_redirect_uri}")
    
    if not config_ok:
        issues_found.append("Google OAuth configuration incomplete")
        fixes.append("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
    
    # 4. Check if there are any unique constraint violations
    print("\n4. 🔒 Checking for Potential Constraint Issues...")
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            # Check for duplicate test data that might cause issues
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(DISTINCT email) as unique_emails,
                    COUNT(DISTINCT username) as unique_usernames,
                    COUNT(DISTINCT google_id) as unique_google_ids
                FROM users 
                WHERE google_id IS NOT NULL
            """))
            
            row = result.fetchone()
            if row:
                total, unique_emails, unique_usernames, unique_google_ids = row
                print(f"   📊 Google users: {total}")
                print(f"   📊 Unique emails: {unique_emails}")
                print(f"   📊 Unique usernames: {unique_usernames}")
                print(f"   📊 Unique Google IDs: {unique_google_ids}")
                
                if total != unique_emails or total != unique_usernames or total != unique_google_ids:
                    print("   ⚠️  Potential duplicate data detected")
                    issues_found.append("Duplicate data in users table")
                    fixes.append("Clean up duplicate users before testing")
                else:
                    print("   ✅ No duplicate data detected")
    except Exception as e:
        print(f"   ❌ Error checking constraints: {e}")
    
  
if __name__ == "__main__":
    check_common_issues()