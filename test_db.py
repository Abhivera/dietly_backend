# test_db.py
from app.core.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        
        # Check existing tables
        tables = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)).fetchall()
        
        print("📋 Existing tables:")
        for table in tables:
            print(f"  - {table[0]}")
            
except Exception as e:
    print(f"❌ Database connection failed: {e}")