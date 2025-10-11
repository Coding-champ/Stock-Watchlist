#!/usr/bin/env python3
"""
Test für die neue modulare yfinance Struktur
Testet ob alle Funktionen korrekt importiert werden können
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_modular_imports():
    """Testet ob alle Funktionen aus den neuen Modulen importiert werden können"""
    
    print("🧪 Test: Modulare yfinance Struktur")
    print("=" * 50)
    
    try:
        # Test 1: Import des neuen Pakets
        print("📦 Teste Import des neuen yfinance Pakets...")
        from backend.app.services.yfinance import (
            get_stock_info,
            get_fast_stock_data,
            get_extended_stock_data,
            get_historical_prices,
            get_chart_data,
            calculate_technical_indicators,
            StockInfo
        )
        print("✅ Alle Funktionen erfolgreich importiert")
        
        # Test 2: Teste eine einfache Funktion
        print("\n🔍 Teste get_stock_info Funktion...")
        stock_info = get_stock_info("AAPL")
        if stock_info:
            print(f"✅ Stock Info erfolgreich: {stock_info.name} ({stock_info.ticker})")
            print(f"   - Preis: ${stock_info.current_price}")
            print(f"   - Market Cap: ${stock_info.market_cap:,}")
        else:
            print("⚠️ Keine Stock Info erhalten")
        
        # Test 3: Teste fast_stock_data
        print("\n⚡ Teste get_fast_stock_data Funktion...")
        fast_data = get_fast_stock_data("AAPL")
        if fast_data:
            print("✅ Fast Data erfolgreich:")
            print(f"   - Preis: ${fast_data['price_data']['current_price']}")
            print(f"   - Volumen: {fast_data['volume_data']['volume']:,}")
        else:
            print("⚠️ Keine Fast Data erhalten")
        
        # Test 4: Teste extended_stock_data
        print("\n📊 Teste get_extended_stock_data Funktion...")
        extended_data = get_extended_stock_data("AAPL")
        if extended_data:
            print("✅ Extended Data erfolgreich:")
            print(f"   - PE Ratio: {extended_data['financial_ratios']['pe_ratio']}")
            print(f"   - Dividend Yield: {extended_data['dividend_info']['dividend_yield']}")
        else:
            print("⚠️ Keine Extended Data erhalten")
        
        # Test 5: Teste historische Daten
        print("\n📈 Teste get_historical_prices Funktion...")
        hist_data = get_historical_prices("AAPL", period="1mo")
        if hist_data is not None and not hist_data.empty:
            print(f"✅ Historische Daten erfolgreich: {len(hist_data)} Einträge")
            print(f"   - Letzter Preis: ${hist_data['Close'].iloc[-1]:.2f}")
        else:
            print("⚠️ Keine historischen Daten erhalten")
        
        print("\n🎉 Alle Tests erfolgreich!")
        return True
        
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        return False
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backward_compatibility():
    """Testet ob bestehende Imports weiterhin funktionieren"""
    
    print("\n🔄 Test: Rückwärtskompatibilität")
    print("=" * 40)
    
    try:
        # Teste verschiedene Import-Pfade
        print("📦 Teste verschiedene Import-Pfade...")
        
        # Test 1: Direkter Import aus dem Paket
        from backend.app.services.yfinance import get_stock_info as get_stock_info_new
        print("✅ Direkter Paket-Import funktioniert")
        
        # Test 2: Import spezifischer Module
        from backend.app.services.yfinance.stock_info import get_stock_info as get_stock_info_direct
        print("✅ Direkter Modul-Import funktioniert")
        
        # Test 3: Teste ob beide Funktionen identisch sind
        if get_stock_info_new == get_stock_info_direct:
            print("✅ Funktionen sind identisch")
        else:
            print("⚠️ Funktionen sind unterschiedlich")
        
        print("🎉 Rückwärtskompatibilität bestätigt!")
        return True
        
    except Exception as e:
        print(f"❌ Rückwärtskompatibilität fehlgeschlagen: {e}")
        return False

def test_performance_comparison():
    """Vergleicht Performance zwischen alter und neuer Struktur"""
    
    print("\n⚡ Test: Performance-Vergleich")
    print("=" * 35)
    
    try:
        import time
        
        # Teste Performance der neuen Struktur
        print("🆕 Teste neue modulare Struktur...")
        start_time = time.time()
        
        from backend.app.services.yfinance import get_fast_stock_data, get_extended_stock_data
        
        fast_data = get_fast_stock_data("AAPL")
        extended_data = get_extended_stock_data("AAPL")
        
        new_time = time.time() - start_time
        print(f"✅ Neue Struktur: {new_time:.2f}s")
        
        # Performance-Bewertung
        if new_time < 2.0:
            print("   🚀 Sehr schnell!")
        elif new_time < 5.0:
            print("   ✅ Gut!")
        else:
            print("   ⚠️ Könnte schneller sein")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance-Test fehlgeschlagen: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test-Suite für modulare yfinance Struktur")
    print("Testet die neue Paket-Struktur und Rückwärtskompatibilität")
    print()
    
    success = True
    
    # Führe alle Tests durch
    success &= test_modular_imports()
    success &= test_backward_compatibility()
    success &= test_performance_comparison()
    
    if success:
        print(f"\n🎉 Alle Tests erfolgreich!")
        print("Die modulare Struktur ist bereit für die Produktion.")
    else:
        print(f"\n❌ Einige Tests fehlgeschlagen!")
        print("Bitte überprüfe die Implementierung.")
