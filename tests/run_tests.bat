@echo off
echo.
echo ===================================
echo    Stock Watchlist Test Runner
echo ===================================
echo.

REM Prüfe ob Python verfügbar ist
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python ist nicht verfügbar oder nicht im PATH
    echo    Bitte installieren Sie Python oder fügen Sie es zum PATH hinzu
    pause
    exit /b 1
)

REM Wechsle zum tests Verzeichnis
cd /d "%~dp0"

echo 🚀 Starte alle Tests...
echo.

REM Führe den Python Test Runner aus
python run_all_tests.py

echo.
echo ✅ Test-Run abgeschlossen!
echo.
pause