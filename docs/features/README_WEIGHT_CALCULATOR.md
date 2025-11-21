# Index Weight Calculator

Automatische Berechnung von Index-Constituent-Gewichtungen basierend auf Marktkapitalisierung oder gleichgewichtet.

### 1. **Market-Cap Weighted** (Standard)
Gewichtung basierend auf Marktkapitalisierung:
```
Weight = (Aktien-Market-Cap / Summe aller Market-Caps) × 100
```

Geeignet für: S&P 500, DAX, NASDAQ-100, etc.

### 2. **Equal Weighted**
Gleiche Gewichtung für alle Constituents:
```
Weight = 100 / Anzahl Constituents
```

Geeignet für: Equal-Weight-Indizes

## Verwendung

### Einzelner Index (Market-Cap)
```powershell
# S&P 500
python tools\calculate_index_weights.py --index "^GSPC"

# DAX
python tools\calculate_index_weights.py --index "^GDAXI"

# NASDAQ-100
python tools\calculate_index_weights.py --index "^NDX"
```

### Alle Indizes
```powershell
python tools\calculate_index_weights.py
```

### Equal-Weight Methode
```powershell
python tools\calculate_index_weights.py --index "^GSPC" --method equal
```

### Dry-Run (Simulation ohne Speichern)
```powershell
# Zeigt Änderungen, speichert aber nicht
python tools\calculate_index_weights.py --index "^GSPC" --dry-run
```

## Parameter

| Parameter | Standard | Beschreibung |
|-----------|----------|--------------|
| `--index` | None (alle) | Index-Ticker (z.B. "^GSPC", "^GDAXI") |
| `--method` | market_cap | Berechnungsmethode: market_cap oder equal |
| `--dry-run` | False | Simulation ohne Speichern |

## Ausgabe-Beispiel

```
2025-11-21 18:00:00 - INFO - Calculating weights for: S&P 500 (^GSPC)
2025-11-21 18:00:00 - INFO - Method: market_cap
============================================================
SUCCESS - S&P 500
============================================================
Updated: 5 constituents
Total Market Cap: $12,345,678,901,234

Top 10 Weights:
   1. AAPL  :   6.50% ->   7.05% (+0.55%)
   2. MSFT  :   6.00% ->   6.45% (+0.45%)
   3. GOOGL :   3.50% ->   3.80% (+0.30%)
   4. NVDA  :   2.80% ->   3.20% (+0.40%)
   5. TSLA  :   1.70% ->   1.85% (+0.15%)
```

## CSV-Upload ohne Gewichtungen

Du kannst jetzt CSVs **ohne** `weight`-Spalte hochladen:

### Minimales CSV-Format
```csv
ticker_symbol,date_added
AAPL,2023-01-01
MSFT,2023-01-01
GOOGL,2023-01-01
```

### Noch einfacher (nur Ticker)
```csv
ticker_symbol
AAPL
MSFT
GOOGL
```

Nach dem Import einfach das Weight-Calculator-Tool ausführen.

## Workflow

### Neuen Index mit Constituents erstellen

1. **CSV vorbereiten** (nur Ticker nötig):
```csv
ticker_symbol
AAPL
MSFT
GOOGL
NVDA
TSLA
```

2. **Import durchführen** (über seed_indices.py oder API)

3. **Gewichtungen berechnen**:
```powershell
python tools\calculate_index_weights.py --index "^GSPC"
```

4. **Fertig!** Gewichtungen sind aktuell und korrekt.

### Regelmäßige Aktualisierung

Für automatische tägliche/wöchentliche Updates:

```powershell
# Windows Task Scheduler (täglich um 18:00 nach Marktschluss US)
# Aktion: python
# Argumente: tools\calculate_index_weights.py
# Start in: D:\Programmieren\Projekte\Produktiv\Web Development\Stock-Watchlist
```

## API Integration (optional)

Der Service kann auch über API-Endpoint aufgerufen werden. Beispiel Route hinzufügen:

```python
# In backend/app/routes/indices.py
@router.post("/{ticker_symbol}/recalculate-weights")
def recalculate_weights(ticker_symbol: str, db: Session = Depends(get_db)):
    calculator = IndexWeightCalculator(db)
    index = index_service.get_index_by_symbol(ticker_symbol)
    result = calculator.calculate_market_cap_weights(index.id)
    return result
```

## Technische Details

### Market-Cap Quelle
- Abruf über **yfinance** API
- Feld: `info['marketCap']`
- Echtzeit-Daten (während Handelszeiten)

### Genauigkeit
- Gewichtungen auf 4 Dezimalstellen gerundet
- Summe aller Gewichtungen ≈ 100%
- Kleine Abweichungen durch Rundung möglich

### Fehlerbehandlung
- Fehlende Market-Caps werden übersprungen
- Mindestens 1 gültige Market-Cap erforderlich
- Detaillierte Fehler-Logs

### Performance
- ~1-2 Sekunden pro Constituent (yfinance Rate-Limit)
- S&P 500 (500 Constituents): ~10-15 Minuten
- DAX 40: ~1-2 Minuten

## Hinweise

⚠️ **Rate-Limits**: yfinance hat Rate-Limits. Bei vielen Constituents dauert die Berechnung länger.

✓ **Best Practice**: 
- Dry-Run vor erster Ausführung
- Regelmäßige Updates (täglich/wöchentlich)
- Nach jedem Constituent-Update ausführen

🔄 **Automatisierung empfohlen**: Task-Scheduler einrichten für regelmäßige Updates
