# Tests & Utilities

Dieser Ordner enthält alle Test-Dateien und Hilfsprogramme für die Stock Watchlist Anwendung.

## 📁 Datei-Übersicht

### 🧪 Test-Dateien

#### `test_api.py`
- **Zweck:** Umfassende API-Tests für alle Endpunkte
- **Features:**
  - Erstellt Test-Watchlists
  - Testet das Hinzufügen von Aktien per Ticker-Symbol
  - Validiert Marktdaten-Updates
  - Prüft Fehlerbehandlung

**Verwendung:**
```bash
cd tests
python test_api.py
```

#### `test_yfinance.py`
- **Zweck:** Vollständige Integration-Tests für yfinance-Funktionalität
- **Features:**
  - Testet Watchlist-Erstellung
  - Aktiensuche und -hinzufügung
  - Marktdaten-Aktualisierung
  - Mehrere Aktien hinzufügen

**Verwendung:**
```bash
cd tests
python test_yfinance.py
```

#### `test_yfinance_simple.py`
- **Zweck:** Einfache Unit-Tests für yfinance-Service
- **Features:**
  - Direkter Test des yfinance-Services
  - Validierung von Aktieninformationen
  - Test mit ungültigen Ticker-Symbolen

**Verwendung:**
```bash
cd tests
python test_yfinance_simple.py
```

### 🔧 Debug & Utility-Dateien

#### `debug_api_data.py`
- **Zweck:** Debuggt die API-Datenstruktur
- **Features:**
  - Prüft JSON-Response-Struktur
  - Analysiert Marktdaten-Format
  - Hilft bei Datenfluß-Problemen

**Verwendung:**
```bash
cd tests
python debug_api_data.py
```

#### `debug_env.py`
- **Zweck:** Debuggt Environment-Variablen und Datenbankverbindung
- **Features:**
  - Prüft .env-Datei-Loading
  - Testet Datenbankverbindung
  - Zeigt alle relevanten Umgebungsvariablen

**Verwendung:**
```bash
cd tests
python debug_env.py
```

#### `init_db.py`
- **Zweck:** Initialisiert die Datenbank mit allen Tabellen
- **Features:**
  - Erstellt alle SQLAlchemy-Tabellen
  - Testet Datenbankverbindung
  - Validiert Schema-Setup

**Verwendung:**
```bash
cd tests
python init_db.py
```

## 🚀 Alle Tests ausführen

### Voraussetzungen
1. Backend-Server läuft auf Port 8000:
   ```bash
   uvicorn backend.app.main:app --reload
   ```

2. Datenbank ist initialisiert:
   ```bash
   cd tests
   python init_db.py
   ```

### Test-Reihenfolge (empfohlen)
1. **Environment & DB:** `python debug_env.py`
2. **Database Init:** `python init_db.py`
3. **yfinance Service:** `python test_yfinance_simple.py`
4. **API Integration:** `python test_api.py`
5. **Full Integration:** `python test_yfinance.py`

## 📊 Test-Abdeckung

- ✅ **Database Connection** - Verbindung zur PostgreSQL-Datenbank
- ✅ **Environment Setup** - .env-Datei und Umgebungsvariablen
- ✅ **yfinance Integration** - Externe API-Aufrufe
- ✅ **REST API Endpoints** - Alle CRUD-Operationen
- ✅ **Error Handling** - Fehlerbehandlung und Validierung
- ✅ **Data Flow** - End-to-End Datenfluss

## 🐛 Debugging

Bei Problemen:
1. Starten Sie mit `debug_env.py` um die Grundkonfiguration zu prüfen
2. Verwenden Sie `debug_api_data.py` um API-Response-Probleme zu analysieren
3. Prüfen Sie die Logs im Backend-Terminal

## 📝 Neue Tests hinzufügen

Beim Hinzufügen neuer Tests:
1. Verwenden Sie aussagekräftige Dateinamen (`test_*.py`)
2. Dokumentieren Sie den Zweck in der Datei
3. Aktualisieren Sie diese README-Datei
4. Stellen Sie sicher, dass Tests unabhängig voneinander laufen können