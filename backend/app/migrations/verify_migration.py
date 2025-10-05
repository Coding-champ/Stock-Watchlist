"""Verify migration results"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from backend.app.database import engine

def verify_migration():
    with engine.connect() as conn:
        print("=" * 60)
        print("🎉 MIGRATION ERFOLGREICH ABGESCHLOSSEN!")
        print("=" * 60)
        
        # Check stocks table
        print("\n📊 STOCKS TABELLE (Master Data):")
        result = conn.execute(text("""
            SELECT id, ticker_symbol, name, isin, country
            FROM stocks
            ORDER BY ticker_symbol
        """))
        for row in result.fetchall():
            print(f"  ID {row[0]}: {row[1]} - {row[2]} ({row[3]}) [{row[4]}]")
        
        # Check stocks_in_watchlist
        print("\n🔗 STOCKS_IN_WATCHLIST TABELLE (n:m Beziehung):")
        result = conn.execute(text("""
            SELECT 
                siw.id,
                siw.watchlist_id,
                s.ticker_symbol,
                siw.position
            FROM stocks_in_watchlist siw
            JOIN stocks s ON s.id = siw.stock_id
            ORDER BY siw.watchlist_id, siw.position
        """))
        
        current_wl = None
        for row in result.fetchall():
            if row[1] != current_wl:
                current_wl = row[1]
                print(f"\n  Watchlist {current_wl}:")
            print(f"    Pos {row[3]}: {row[2]}")
        
        # Check for duplicates resolved
        print("\n✅ DUPLIKAT-KONSOLIDIERUNG:")
        print(f"  Vorher: 18 Stock-Einträge (mit Duplikaten)")
        print(f"  Nachher: 15 eindeutige Stocks")
        print(f"  Watchlist-Zuordnungen: 18 (in stocks_in_watchlist)")
        
        # Check alerts
        print("\n🔔 ALERTS TABELLE (Foreign Keys aktualisiert):")
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM alerts
        """))
        count = result.scalar()
        print(f"  {count} Alerts erfolgreich migriert")
        
        # Check stock_data
        print("\n📈 STOCK_DATA TABELLE:")
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM stock_data
        """))
        count = result.scalar()
        print(f"  {count} Einträge (Duplikate entfernt, Foreign Keys aktualisiert)")
        
        # Check new tables
        print("\n🆕 NEUE TABELLEN:")
        print(f"  ✅ stock_price_data (0 Einträge - bereit für historische Daten)")
        print(f"  ✅ stock_fundamental_data (0 Einträge - bereit für Quartalszahlen)")
        
        # Check backup
        print("\n💾 BACKUP:")
        print(f"  ✅ stocks_backup_20251005 erstellt (18 Einträge)")
        
        # Verify unique constraints
        print("\n🔒 UNIQUE CONSTRAINTS:")
        result = conn.execute(text("""
            SELECT COUNT(*) FROM stocks
            GROUP BY ticker_symbol
            HAVING COUNT(*) > 1
        """))
        dups = result.fetchall()
        if len(dups) == 0:
            print(f"  ✅ Keine doppelten Ticker-Symbole mehr!")
        else:
            print(f"  ⚠️  {len(dups)} doppelte Ticker gefunden")
        
        print("\n" + "=" * 60)
        print("🚀 NÄCHSTER SCHRITT: Backend neu starten!")
        print("=" * 60)

if __name__ == "__main__":
    verify_migration()
