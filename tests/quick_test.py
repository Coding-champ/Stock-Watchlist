#!/usr/bin/env python3
"""
Quick Test Script - Führt nur die wichtigsten Tests aus
"""

import subprocess
import sys
import os
from pathlib import Path

def run_test(script_name, description):
    """Führt einen einzelnen Test aus"""
    print(f"\n🧪 {description}")
    print("-" * 40)
    
    try:
        os.chdir(Path(__file__).parent)
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"✅ ERFOLGREICH")
            return True
        else:
            print(f"❌ FEHLER")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        return False

def main():
    print("🚀 Stock Watchlist - Quick Test")
    print("=" * 40)
    
    # Nur die wichtigsten Tests
    tests = [
        ("debug_env.py", "Environment & Database Check"),
        ("test_yfinance_simple.py", "yfinance Service Test"),
    ]
    
    success = 0
    for test_file, description in tests:
        if run_test(test_file, description):
            success += 1
    
    print(f"\n📊 Ergebnis: {success}/{len(tests)} Tests erfolgreich")
    
    if success == len(tests):
        print("🎉 Grundkonfiguration ist OK!")
        print("Führen Sie 'python run_all_tests.py' für komplette Tests aus.")
    else:
        print("⚠️ Bitte prüfen Sie die Konfiguration.")
    
    return success == len(tests)

if __name__ == "__main__":
    main()