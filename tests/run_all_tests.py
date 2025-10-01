#!/usr/bin/env python3
"""
Test Runner Script für Stock Watchlist
Führt alle Tests in der optimalen Reihenfolge aus
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(command, description):
    """Führt einen Befehl aus und zeigt das Ergebnis an"""
    print(f"\n{'='*50}")
    print(f"🧪 {description}")
    print(f"{'='*50}")
    
    try:
        # Wechsle zum tests Verzeichnis
        os.chdir(Path(__file__).parent)
        
        result = subprocess.run([sys.executable, command], 
                              capture_output=True, 
                              text=True, 
                              timeout=60)
        
        if result.returncode == 0:
            print(f"✅ {description} - ERFOLGREICH")
            if result.stdout:
                print(f"Output:\n{result.stdout}")
        else:
            print(f"❌ {description} - FEHLER")
            if result.stderr:
                print(f"Error:\n{result.stderr}")
            if result.stdout:
                print(f"Output:\n{result.stdout}")
                
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT (>60s)")
        return False
    except Exception as e:
        print(f"💥 {description} - EXCEPTION: {e}")
        return False

def check_server():
    """Prüft ob der Backend-Server läuft"""
    try:
        import requests
        response = requests.get("http://localhost:8000/docs", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Hauptfunktion - führt alle Tests aus"""
    print("🚀 Stock Watchlist Test Runner")
    print("=" * 50)
    
    # Prüfe ob Backend läuft
    if not check_server():
        print("❌ Backend-Server läuft nicht auf http://localhost:8000")
        print("   Bitte starten Sie den Server mit:")
        print("   uvicorn backend.app.main:app --reload")
        print("\n   Oder verwenden Sie das start.sh Script")
        return False
    
    print("✅ Backend-Server läuft auf http://localhost:8000")
    
    # Test-Reihenfolge
    tests = [
        ("debug_env.py", "Environment & Database Connection Check"),
        ("init_db.py", "Database Initialization"),
        ("test_yfinance_simple.py", "yfinance Service Unit Tests"),
        ("test_api.py", "API Integration Tests"),
        ("test_yfinance.py", "Full yfinance Integration Tests"),
        ("debug_api_data.py", "API Data Structure Debug")
    ]
    
    success_count = 0
    total_tests = len(tests)
    
    # Führe Tests aus
    for test_file, description in tests:
        if run_command(test_file, description):
            success_count += 1
        time.sleep(1)  # Kurze Pause zwischen Tests
    
    # Zusammenfassung
    print(f"\n{'='*50}")
    print("📊 TEST ZUSAMMENFASSUNG")
    print(f"{'='*50}")
    print(f"✅ Erfolgreich: {success_count}/{total_tests}")
    print(f"❌ Fehlgeschlagen: {total_tests - success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("\n🎉 ALLE TESTS ERFOLGREICH! 🎉")
        print("Ihre Stock Watchlist Anwendung ist bereit für den Einsatz!")
        return True
    else:
        print(f"\n⚠️  {total_tests - success_count} Test(s) fehlgeschlagen")
        print("Bitte prüfen Sie die Fehlermeldungen oben.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)