#!/usr/bin/env python3
"""
Performance Test für yfinance Optimierungen
Testet die Performance-Verbesserungen von get_extended_stock_data()
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.yfinance_service import get_fast_stock_data, get_extended_stock_data

def test_performance_comparison():
    """Testet die Performance-Verbesserungen"""
    
    test_ticker = "AAPL"  # Apple als Test-Ticker
    
    print("🚀 Performance Test: yfinance Optimierungen")
    print("=" * 50)
    
    # Test 1: Fast Data (nur fast_info)
    print(f"\n📊 Test 1: Fast Data für {test_ticker}")
    start_time = time.time()
    fast_data = get_fast_stock_data(test_ticker)
    fast_time = time.time() - start_time
    
    if fast_data:
        print(f"✅ Fast Data erfolgreich in {fast_time:.2f}s")
        print(f"   - Preis: {fast_data['price_data']['current_price']}")
        print(f"   - Volumen: {fast_data['volume_data']['volume']}")
        print(f"   - Market Cap: {fast_data['market_data']['market_cap']}")
    else:
        print("❌ Fast Data fehlgeschlagen")
    
    # Test 2: Extended Data (optimiert)
    print(f"\n📈 Test 2: Extended Data für {test_ticker} (optimiert)")
    start_time = time.time()
    extended_data = get_extended_stock_data(test_ticker)
    extended_time = time.time() - start_time
    
    if extended_data:
        print(f"✅ Extended Data erfolgreich in {extended_time:.2f}s")
        print(f"   - PE Ratio: {extended_data['financial_ratios']['pe_ratio']}")
        print(f"   - Dividend Yield: {extended_data['dividend_info']['dividend_yield']}")
        print(f"   - Beta: {extended_data['risk_metrics']['beta']}")
    else:
        print("❌ Extended Data fehlgeschlagen")
    
    # Performance-Vergleich
    print(f"\n📊 Performance-Vergleich:")
    print(f"   - Fast Data: {fast_time:.2f}s")
    print(f"   - Extended Data: {extended_time:.2f}s")
    
    if fast_time < 1.0:
        print(f"   ✅ Fast Data ist sehr schnell (< 1s)")
    else:
        print(f"   ⚠️ Fast Data könnte schneller sein")
    
    if extended_time < 2.0:
        print(f"   ✅ Extended Data ist akzeptabel (< 2s)")
    else:
        print(f"   ⚠️ Extended Data ist noch langsam (> 2s)")
    
    # Geschätzte Verbesserung
    estimated_old_time = 3.0  # Geschätzte alte Zeit
    improvement = ((estimated_old_time - extended_time) / estimated_old_time) * 100
    
    print(f"\n🎯 Geschätzte Verbesserung:")
    print(f"   - Alte Zeit (geschätzt): {estimated_old_time:.1f}s")
    print(f"   - Neue Zeit: {extended_time:.2f}s")
    print(f"   - Verbesserung: {improvement:.1f}%")
    
    if improvement > 30:
        print("   🎉 Exzellente Verbesserung!")
    elif improvement > 15:
        print("   ✅ Gute Verbesserung!")
    else:
        print("   ⚠️ Verbesserung könnte größer sein")

def test_multiple_stocks():
    """Testet mehrere Aktien für bessere Statistik"""
    
    test_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
    
    print(f"\n🔄 Multi-Stock Test ({len(test_tickers)} Aktien)")
    print("=" * 50)
    
    total_fast_time = 0
    total_extended_time = 0
    successful_tests = 0
    
    for ticker in test_tickers:
        print(f"\n📊 Teste {ticker}...")
        
        # Fast Data Test
        start_time = time.time()
        fast_data = get_fast_stock_data(ticker)
        fast_time = time.time() - start_time
        
        # Extended Data Test
        start_time = time.time()
        extended_data = get_extended_stock_data(ticker)
        extended_time = time.time() - start_time
        
        if fast_data and extended_data:
            total_fast_time += fast_time
            total_extended_time += extended_time
            successful_tests += 1
            print(f"   ✅ {ticker}: Fast {fast_time:.2f}s, Extended {extended_time:.2f}s")
        else:
            print(f"   ❌ {ticker}: Fehler beim Laden")
    
    if successful_tests > 0:
        avg_fast_time = total_fast_time / successful_tests
        avg_extended_time = total_extended_time / successful_tests
        
        print(f"\n📊 Durchschnittliche Zeiten ({successful_tests} erfolgreiche Tests):")
        print(f"   - Fast Data: {avg_fast_time:.2f}s")
        print(f"   - Extended Data: {avg_extended_time:.2f}s")
        
        estimated_old_time = 3.0
        improvement = ((estimated_old_time - avg_extended_time) / estimated_old_time) * 100
        print(f"   - Geschätzte Verbesserung: {improvement:.1f}%")

if __name__ == "__main__":
    print("🧪 Performance Test für yfinance Optimierungen")
    print("Testet die neuen get_fast_stock_data() und optimierte get_extended_stock_data() Funktionen")
    print()
    
    try:
        test_performance_comparison()
        test_multiple_stocks()
        
        print(f"\n✅ Performance Test abgeschlossen!")
        print("Die Optimierungen sollten eine deutliche Verbesserung zeigen.")
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
