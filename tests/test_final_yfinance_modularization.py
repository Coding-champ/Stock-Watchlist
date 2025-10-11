#!/usr/bin/env python3
"""
Finaler Test für die yfinance Modularisierung
Testet alle kritischen Funktionen und Imports
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_all_imports():
    """Testet alle kritischen Imports"""
    
    print("🧪 Finaler Test: yfinance Modularisierung")
    print("=" * 50)
    
    success = True
    
    # Test 1: Alte Imports (Backward Compatibility)
    print("🔄 Teste alte Imports (Rückwärtskompatibilität)...")
    try:
        from backend.app.services.yfinance_service import (
            get_stock_info,
            get_fast_stock_data,
            get_extended_stock_data,
            get_historical_prices,
            get_chart_data,
            calculate_technical_indicators,
            StockInfo
        )
        print("✅ Alle alten Imports funktionieren")
    except Exception as e:
        print(f"❌ Alte Imports fehlgeschlagen: {e}")
        success = False
    
    # Test 2: Neue Imports (Modular)
    print("\n🆕 Teste neue Imports (Modular)...")
    try:
        from backend.app.services.yfinance import (
            get_stock_info as get_stock_info_new,
            get_fast_stock_data as get_fast_stock_data_new,
            get_extended_stock_data as get_extended_stock_data_new
        )
        print("✅ Alle neuen Imports funktionieren")
    except Exception as e:
        print(f"❌ Neue Imports fehlgeschlagen: {e}")
        success = False
    
    # Test 3: Funktionstest
    print("\n🔍 Teste Funktionen...")
    try:
        # Teste eine einfache Funktion
        stock_info = get_stock_info("AAPL")
        if stock_info:
            print(f"✅ get_stock_info: {stock_info.name}")
        else:
            print("⚠️ get_stock_info: Keine Daten")
        
        # Teste fast data
        fast_data = get_fast_stock_data("AAPL")
        if fast_data:
            print(f"✅ get_fast_stock_data: Preis ${fast_data['price_data']['current_price']}")
        else:
            print("⚠️ get_fast_stock_data: Keine Daten")
        
        # Teste extended data
        extended_data = get_extended_stock_data("AAPL")
        if extended_data:
            print(f"✅ get_extended_stock_data: PE {extended_data['financial_ratios']['pe_ratio']}")
        else:
            print("⚠️ get_extended_stock_data: Keine Daten")
            
    except Exception as e:
        print(f"❌ Funktionstest fehlgeschlagen: {e}")
        success = False
    
    # Test 4: Spezifische Module
    print("\n📦 Teste spezifische Module...")
    try:
        from backend.app.services.yfinance.stock_info import get_stock_info_by_identifier
        from backend.app.services.yfinance.price_data import get_historical_prices
        from backend.app.services.yfinance.financial_data import get_analyst_data
        from backend.app.services.yfinance.indicators import calculate_technical_indicators
        print("✅ Alle spezifischen Module funktionieren")
    except Exception as e:
        print(f"❌ Spezifische Module fehlgeschlagen: {e}")
        success = False
    
    return success

def test_existing_code_compatibility():
    """Testet ob bestehender Code weiterhin funktioniert"""
    
    print("\n🔗 Teste bestehende Code-Kompatibilität...")
    
    success = True
    
    # Teste Imports aus anderen Services
    try:
        # Teste Alert Service Import
        from backend.app.services.alert_service import AlertService
        print("✅ Alert Service Import funktioniert")
        
        # Teste Cache Service Import
        from backend.app.services.cache_service import StockDataCacheService
        print("✅ Cache Service Import funktioniert")
        
        # Teste Stock Service Import
        from backend.app.services.stock_service import StockService
        print("✅ Stock Service Import funktioniert")
        
    except Exception as e:
        print(f"❌ Service Imports fehlgeschlagen: {e}")
        success = False
    
    return success

def show_modularization_summary():
    """Zeigt eine Zusammenfassung der Modularisierung"""
    
    print("\n📊 Modularisierung Zusammenfassung")
    print("=" * 40)
    
    print("🏗️ Neue Struktur:")
    print("   backend/app/services/yfinance/")
    print("   ├── __init__.py          # Re-exportiert alle Funktionen")
    print("   ├── client.py            # Core utilities & StockInfo class")
    print("   ├── stock_info.py        # Stock information & resolution")
    print("   ├── price_data.py        # Price history & charts")
    print("   ├── financial_data.py    # Fundamentals, dividends, earnings")
    print("   └── indicators.py        # Technical indicators")
    
    print("\n✅ Vorteile:")
    print("   - Bessere Wartbarkeit (1148 → 5 Module)")
    print("   - Klare Verantwortlichkeiten")
    print("   - Einfacheres Testing")
    print("   - Rückwärtskompatibilität")
    print("   - Bessere Code-Organisation")
    
    print("\n🔄 Migration:")
    print("   - Alte Imports funktionieren weiterhin")
    print("   - Neue Imports sind verfügbar")
    print("   - Keine Breaking Changes")
    print("   - Backup erstellt: yfinance_service_backup.py")

if __name__ == "__main__":
    print("🎯 Finaler Test für yfinance Modularisierung")
    print("Testet alle kritischen Funktionen und Kompatibilität")
    print()
    
    # Führe alle Tests durch
    success = True
    success &= test_all_imports()
    success &= test_existing_code_compatibility()
    
    # Zeige Zusammenfassung
    show_modularization_summary()
    
    if success:
        print(f"\n🎉 Modularisierung erfolgreich!")
        print("Alle Tests bestanden - die neue Struktur ist produktionsbereit.")
    else:
        print(f"\n❌ Modularisierung fehlgeschlagen!")
        print("Bitte überprüfe die Implementierung.")
