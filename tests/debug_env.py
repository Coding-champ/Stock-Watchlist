#!/usr/bin/env python3
"""
Test script to debug environment variable loading
"""

import os
from dotenv import load_dotenv

print("Testing environment variable loading...")
print("Current working directory:", os.getcwd())

# Try to load .env file
load_dotenv()

print("DATABASE_URL from environment:", os.getenv("DATABASE_URL"))
print("All environment variables related to database:")
for key, value in os.environ.items():
    if "DATABASE" in key.upper() or "DB" in key.upper():
        print(f"  {key} = {value}")

# Test database connection
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from backend.app.database import engine
    from sqlalchemy import text
    
    print("\nTesting database connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print(f"Error type: {type(e)}")