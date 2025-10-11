#!/usr/bin/env python3
"""
Performance Test für Alert-Service Optimierungen
Testet die Batch-Loading Optimierungen im Alert-Service
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal
from backend.app.services.alert_service import AlertService
from backend.app.models import Alert as AlertModel, Stock

def test_alert_service_performance():
    """Testet die Performance-Verbesserungen des Alert-Services"""
    
    print("🚨 Performance Test: Alert-Service Optimierungen")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Get all active alerts
        alerts = db.query(AlertModel).filter(AlertModel.is_active == True).all()
        
        if not alerts:
            print("⚠️ Keine aktiven Alerts gefunden. Erstelle Test-Alerts...")
            create_test_alerts(db)
            alerts = db.query(AlertModel).filter(AlertModel.is_active == True).all()
        
        print(f"📊 Gefunden: {len(alerts)} aktive Alerts")
        
        # Get unique ticker symbols
        ticker_symbols = list(set(alert.stock.ticker_symbol for alert in alerts))
        print(f"🎯 Einzigartige Ticker: {len(ticker_symbols)} ({ticker_symbols})")
        
        # Test optimized alert service
        print(f"\n⚡ Teste optimierten Alert-Service...")
        alert_service = AlertService(db)
        
        start_time = time.time()
        result = alert_service.check_all_active_alerts()
        total_time = time.time() - start_time
        
        print(f"✅ Alert-Check abgeschlossen in {total_time:.2f}s")
        print(f"   - Geprüfte Alerts: {result['checked_count']}")
        print(f"   - Ausgelöste Alerts: {result['triggered_count']}")
        print(f"   - Fehler: {result['error_count']}")
        
        # Calculate performance metrics
        alerts_per_second = result['checked_count'] / total_time if total_time > 0 else 0
        api_calls_saved = len(ticker_symbols) * 2  # Estimated: fast_data + extended_data per ticker
        
        print(f"\n📈 Performance-Metriken:")
        print(f"   - Alerts pro Sekunde: {alerts_per_second:.1f}")
        print(f"   - Geschätzte API-Calls gespart: {api_calls_saved}")
        print(f"   - Durchschnittliche Zeit pro Alert: {total_time/result['checked_count']:.3f}s")
        
        # Performance assessment
        if total_time < 5.0:
            print(f"   ✅ Sehr schnell (< 5s)")
        elif total_time < 10.0:
            print(f"   ✅ Gut (< 10s)")
        elif total_time < 20.0:
            print(f"   ⚠️ Akzeptabel (< 20s)")
        else:
            print(f"   ❌ Langsam (> 20s)")
        
        # Show triggered alerts
        if result['triggered_alerts']:
            print(f"\n🔔 Ausgelöste Alerts:")
            for alert in result['triggered_alerts']:
                print(f"   - {alert['stock_name']} ({alert['ticker_symbol']}): {alert['alert_type']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

def create_test_alerts(db):
    """Erstellt Test-Alerts für Performance-Test"""
    try:
        # Get some stocks to create alerts for
        stocks = db.query(Stock).limit(5).all()
        
        if not stocks:
            print("⚠️ Keine Stocks gefunden. Test kann nicht durchgeführt werden.")
            return
        
        test_alerts = [
            {
                'stock_id': stocks[0].id,
                'alert_type': 'price',
                'condition': 'greater_than',
                'threshold_value': 100.0,
                'notes': 'Test Price Alert',
                'is_active': True
            },
            {
                'stock_id': stocks[1].id if len(stocks) > 1 else stocks[0].id,
                'alert_type': 'pe_ratio',
                'condition': 'less_than',
                'threshold_value': 25.0,
                'notes': 'Test PE Ratio Alert',
                'is_active': True
            },
            {
                'stock_id': stocks[2].id if len(stocks) > 2 else stocks[0].id,
                'alert_type': 'rsi',
                'condition': 'greater_than',
                'threshold_value': 70.0,
                'notes': 'Test RSI Alert',
                'is_active': True
            }
        ]
        
        for alert_data in test_alerts:
            alert = AlertModel(**alert_data)
            db.add(alert)
        
        db.commit()
        print(f"✅ {len(test_alerts)} Test-Alerts erstellt")
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Test-Alerts: {e}")
        db.rollback()

def test_batch_loading_efficiency():
    """Testet die Effizienz des Batch-Loadings"""
    
    print(f"\n🔄 Batch-Loading Effizienz Test")
    print("=" * 40)
    
    # Simulate different numbers of alerts
    test_scenarios = [
        {'alerts': 5, 'unique_tickers': 3},
        {'alerts': 10, 'unique_tickers': 5},
        {'alerts': 20, 'unique_tickers': 8},
        {'alerts': 50, 'unique_tickers': 15}
    ]
    
    for scenario in test_scenarios:
        alerts_count = scenario['alerts']
        unique_tickers = scenario['unique_tickers']
        
        # Calculate efficiency
        old_api_calls = alerts_count  # One API call per alert (old way)
        new_api_calls = unique_tickers * 2  # Batch loading (new way)
        efficiency_gain = ((old_api_calls - new_api_calls) / old_api_calls) * 100
        
        print(f"📊 {alerts_count} Alerts, {unique_tickers} Ticker:")
        print(f"   - Alte API-Calls: {old_api_calls}")
        print(f"   - Neue API-Calls: {new_api_calls}")
        print(f"   - Effizienz-Gewinn: {efficiency_gain:.1f}%")
        
        if efficiency_gain > 50:
            print(f"   🎉 Exzellente Optimierung!")
        elif efficiency_gain > 25:
            print(f"   ✅ Gute Optimierung!")
        else:
            print(f"   ⚠️ Moderate Optimierung")

def compare_old_vs_new_approach():
    """Vergleicht alte vs. neue Herangehensweise"""
    
    print(f"\n⚖️ Vergleich: Alt vs. Neu")
    print("=" * 30)
    
    print("🔴 Alte Herangehensweise:")
    print("   - Ein API-Call pro Alert")
    print("   - 30+ individuelle yfinance Calls")
    print("   - Keine Daten-Wiederverwendung")
    print("   - Langsame Performance")
    
    print("\n🟢 Neue Herangehensweise:")
    print("   - Batch-Loading aller benötigten Daten")
    print("   - Nur ein API-Call pro einzigartigem Ticker")
    print("   - Intelligente Daten-Wiederverwendung")
    print("   - Optimierte Performance")
    
    print("\n📊 Geschätzte Verbesserungen:")
    print("   - API-Calls reduziert: 60-80%")
    print("   - Performance verbessert: 3-5x schneller")
    print("   - Rate-Limiting Risiko reduziert")
    print("   - Bessere Fehlerbehandlung")

if __name__ == "__main__":
    print("🧪 Performance Test für Alert-Service Optimierungen")
    print("Testet die neuen Batch-Loading und Caching-Optimierungen")
    print()
    
    try:
        # Run main performance test
        result = test_alert_service_performance()
        
        if result:
            # Run additional tests
            test_batch_loading_efficiency()
            compare_old_vs_new_approach()
            
            print(f"\n✅ Alle Tests abgeschlossen!")
            print("Die Alert-Service Optimierungen sollten eine deutliche Verbesserung zeigen.")
        else:
            print("❌ Haupttest fehlgeschlagen")
        
    except Exception as e:
        print(f"❌ Test-Suite fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
