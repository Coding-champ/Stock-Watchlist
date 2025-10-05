"""
Python-Skript zum Ausführen der Datenbank-Migration für das Alert-System
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect

# Hole DATABASE_URL aus Umgebungsvariablen oder verwende Standard
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/stock_watchlist")

print("🔧 Alert-System Migration")
print("=" * 60)
print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'localhost'}")
print()

try:
    # Erstelle Engine
    engine = create_engine(DATABASE_URL)
    
    # Teste Verbindung
    print("1. Testing database connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"   ✅ Connected to PostgreSQL")
        print(f"   Version: {version.split(',')[0]}")
    
    # Prüfe aktuelle Struktur
    print("\n2. Checking current alerts table structure...")
    inspector = inspect(engine)
    columns = inspector.get_columns('alerts')
    
    existing_columns = [col['name'] for col in columns]
    print(f"   Current columns: {', '.join(existing_columns)}")
    
    needs_expiry_date = 'expiry_date' not in existing_columns
    needs_notes = 'notes' not in existing_columns
    
    if not needs_expiry_date and not needs_notes:
        print("   ℹ️  Migration already applied!")
        print("\n   All required columns exist:")
        print("   - expiry_date ✅")
        print("   - notes ✅")
        sys.exit(0)
    
    # Führe Migration aus
    print("\n3. Applying migration...")
    with engine.connect() as conn:
        if needs_expiry_date:
            print("   Adding column: expiry_date...")
            conn.execute(text("ALTER TABLE alerts ADD COLUMN expiry_date TIMESTAMP NULL;"))
            conn.commit()
            print("   ✅ expiry_date added")
        
        if needs_notes:
            print("   Adding column: notes...")
            conn.execute(text("ALTER TABLE alerts ADD COLUMN notes TEXT NULL;"))
            conn.commit()
            print("   ✅ notes added")
    
    # Verifiziere Migration
    print("\n4. Verifying migration...")
    inspector = inspect(engine)
    columns = inspector.get_columns('alerts')
    final_columns = [col['name'] for col in columns]
    
    print("   Final structure:")
    for col in columns:
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        print(f"   - {col['name']:20} {str(col['type']):20} {nullable}")
    
    print("\n" + "=" * 60)
    print("✅ Migration completed successfully!")
    print("\n💡 Next steps:")
    print("   1. Restart your backend server")
    print("   2. Test the alert creation in the frontend")
    
except Exception as e:
    print(f"\n❌ Migration failed: {e}")
    print("\n💡 Troubleshooting:")
    print("   1. Check if PostgreSQL is running")
    print("   2. Verify DATABASE_URL environment variable")
    print("   3. Check database credentials")
    print(f"\n   Current DATABASE_URL: {DATABASE_URL}")
    sys.exit(1)
