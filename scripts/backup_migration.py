"""
Backup and test migration script
"""
import shutil
import os
from datetime import datetime
from pathlib import Path

# Database path
DB_PATH = Path("stock_watchlist.db")
BACKUP_DIR = Path("backups")

def create_backup():
    """Create a timestamped backup of the database"""
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return None
    
    # Create backup directory
    BACKUP_DIR.mkdir(exist_ok=True)
    
    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"stock_watchlist_{timestamp}_pre_migration.db"
    
    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def restore_backup(backup_path):
    """Restore database from backup"""
    if not backup_path or not Path(backup_path).exists():
        print(f"❌ Backup not found: {backup_path}")
        return False
    
    try:
        shutil.copy2(backup_path, DB_PATH)
        print(f"✅ Database restored from: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "backup":
            create_backup()
        elif sys.argv[1] == "restore" and len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        else:
            print("Usage: python backup_migration.py [backup|restore <backup_file>]")
    else:
        # Default: create backup
        backup_path = create_backup()
        if backup_path:
            print(f"\n🔄 Now you can run the migration:")
            print(f"   python backend/app/migrations/20251005_refactor_stock_tables.py")
            print(f"\n⏪ To rollback:")
            print(f"   python backup_migration.py restore {backup_path}")
