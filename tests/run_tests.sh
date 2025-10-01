#!/bin/bash

echo ""
echo "==================================="
echo "   Stock Watchlist Test Runner"
echo "==================================="
echo ""

# Prüfe ob Python verfügbar ist
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 ist nicht verfügbar"
    echo "   Bitte installieren Sie Python3"
    exit 1
fi

# Wechsle zum tests Verzeichnis
cd "$(dirname "$0")"

echo "🚀 Starte alle Tests..."
echo ""

# Führe den Python Test Runner aus
python3 run_all_tests.py

echo ""
echo "✅ Test-Run abgeschlossen!"
echo ""