# Load Constituent Prices Tool

Dieses Tool lädt historische Preisdaten für Index-Bestandteile (Constituents) in die `asset_price_data` Tabelle.

## Problem
Das TopFlops-Feature benötigt Preisdaten für Constituent-Aktien. Beim initialen Seeding werden nur Index-Preise geladen, aber keine Constituent-Preise.

## Lösung
Das `load_constituent_prices.py` Skript lädt automatisch Preisdaten für alle Constituents eines oder mehrerer Indizes.

## Verwendung

### Alle Indizes (alle Constituents)
```powershell
python tools\load_constituent_prices.py
```

### Spezifischer Index
```powershell
python tools\load_constituent_prices.py --index "^GSPC"
python tools\load_constituent_prices.py --index "^GDAXI"
```

### Mit Zeitraum
```powershell
# Letzter Monat (Standard)
python tools\load_constituent_prices.py --index "^GSPC" --period 1mo

# Letztes Jahr
python tools\load_constituent_prices.py --index "^GSPC" --period 1y

# Maximaler Verlauf
python tools\load_constituent_prices.py --index "^GSPC" --period max
```

### Testmodus (nur erste N Constituents)
```powershell
python tools\load_constituent_prices.py --index "^GSPC" --limit 10
```

## Parameter

| Parameter | Standard | Beschreibung |
|-----------|----------|--------------|
| `--index` | None (alle) | Index-Ticker-Symbol (z.B. "^GSPC", "^GDAXI") |
| `--period` | 1mo | Zeitraum: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max |
| `--interval` | 1d | Intervall: 1d, 1wk, 1mo |
| `--limit` | None (alle) | Max. Anzahl Constituents pro Index (für Tests) |

## Beispiele

```powershell
# S&P 500 Constituents (letzten Monat)
python tools\load_constituent_prices.py --index "^GSPC" --period 1mo

# DAX Constituents (letztes Jahr)
python tools\load_constituent_prices.py --index "^GDAXI" --period 1y

# Alle Indizes, nur 5 Constituents pro Index (Quick-Test)
python tools\load_constituent_prices.py --limit 5

# Maximaler Verlauf für S&P 500 (dauert länger!)
python tools\load_constituent_prices.py --index "^GSPC" --period max
```

## Nach dem Ausführen

Nach dem erfolgreichen Laden sollte das TopFlops-Feature im Frontend funktionieren:
1. Öffne eine Index-Detailseite (z.B. S&P 500)
2. Scrolle zum "Tops / Flops des Tages" Bereich
3. Die Top 5 Gewinner und Verlierer des Tages werden angezeigt

## Automatisierung (optional)

Für regelmäßige Aktualisierung kann das Skript als Cron-Job oder Task geplant werden:

```powershell
# Windows Task Scheduler (täglich um 18:00 nach Marktschluss)
# Aktion: python
# Argumente: tools\load_constituent_prices.py --period 1d
# Start in: D:\Programmieren\Projekte\Produktiv\Web Development\Stock-Watchlist
```

## Hinweise

- Das Skript nutzt yfinance für Datenabruf (Rate-Limits beachten)
- Bei vielen Constituents kann das Laden einige Minuten dauern
- Bereits vorhandene Daten werden überschrieben/aktualisiert
- Die Daten werden in `asset_price_data` mit `asset_type='stock'` gespeichert
