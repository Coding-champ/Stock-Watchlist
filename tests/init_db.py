#!/usr/bin/env python3
"""
Database initialization script
Creates all tables based on SQLAlchemy models
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import engine, Base
from backend.app.models import Watchlist, Stock, StockData, Alert

def create_tables():
    """Create all database tables"""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Test connection
        from backend.app.database import SessionLocal
        db = SessionLocal()
        try:
            # Try a simple query to verify connection
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            print("✅ Database connection test successful!")
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    create_tables()