# Automatische Gewichtungs-Updates

## Übersicht

Dieses Dokumentation beschreibt verschiedene Wege, wie Constituent-Gewichtungen automatisch aktualisiert werden können.

## Option 1: Automatisch beim CSV-Import (Standard)

**Standard-Verhalten:** Beim Import von Constituents via CSV wird automatisch die Gewichtung berechnet.

### API-Nutzung

```bash
POST /api/v1/indices/{ticker_symbol}/constituents/import
```

**Query-Parameter:**
- `auto_calculate_weights` (default: `true`) - Gewichtung automatisch berechnen
- `weight_method` (default: `market_cap`) - Berechnungsmethode
  - `market_cap`: Basierend auf Marktkapitalisierung
  - `equal`: Gleichgewichtung
- `replace_existing` (default: `false`) - Bestehende Constituents ersetzen

**Beispiel:**
```bash
curl -X POST "http://localhost:8000/api/v1/indices/^GSPC/constituents/import?auto_calculate_weights=true&weight_method=market_cap" \
  -F "file=@sp500_constituents.csv"
```

**CSV-Format:**
```csv
ticker_symbol,date_added
AAPL,2024-01-01
MSFT,2024-01-01
GOOGL,2024-01-01
```

**Hinweis:** Die `weight`-Spalte ist optional und kann weggelassen werden, wenn `auto_calculate_weights=true`.

### Response

```json
{
  "success": true,
  "imported": 3,
  "skipped": 0,
  "errors": [],
  "weights_calculated": true,
  "weights_method": "market_cap",
  "weights_updated": 3,
  "total_market_cap": 8500000000000
}
```

## Option 2: Manuelles Update via API

**Endpoint:** Gewichtungen können jederzeit manuell neu berechnet werden.

```bash
POST /api/v1/indices/{ticker_symbol}/constituents/recalculate-weights
```

**Query-Parameter:**
- `method` (default: `market_cap`) - Berechnungsmethode
- `refresh_market_caps` (default: `true`) - Market-Cap-Daten von yfinance aktualisieren

**Beispiele:**

```bash
# S&P 500 mit Market Cap
curl -X POST "http://localhost:8000/api/v1/indices/^GSPC/constituents/recalculate-weights?method=market_cap"

# DAX mit Equal Weight
curl -X POST "http://localhost:8000/api/v1/indices/^GDAXI/constituents/recalculate-weights?method=equal"

# Ohne yfinance-Refresh (nutzt gecachte Market Caps)
curl -X POST "http://localhost:8000/api/v1/indices/^GSPC/constituents/recalculate-weights?refresh_market_caps=false"
```

**Response:**
```json
{
  "success": true,
  "index": "S&P 500",
  "method": "market_cap",
  "updated_count": 5,
  "total_market_cap": 16789314338816,
  "weights": [
    {"ticker": "NVDA", "weight": 25.95},
    {"ticker": "AAPL", "weight": 23.88},
    {"ticker": "GOOGL", "weight": 21.46},
    {"ticker": "MSFT", "weight": 20.91},
    {"ticker": "TSLA", "weight": 7.81}
  ]
}
```

## Option 3: CLI-Tool

**Script:** `tools/calculate_index_weights.py`

```bash
# Einzelner Index
python tools/calculate_index_weights.py --index "^GSPC"

# Mit Dry-Run (keine Änderungen)
python tools/calculate_index_weights.py --index "^GSPC" --dry-run

# Equal-Weight Methode
python tools/calculate_index_weights.py --index "^GSPC" --method equal

# Alle Indices
python tools/calculate_index_weights.py --index "^GSPC"
python tools/calculate_index_weights.py --index "^GDAXI"
python tools/calculate_index_weights.py --index "^NDX"
```

## Option 4: Scheduled Tasks (Empfohlen für regelmäßige Updates)

### Windows Task Scheduler

**PowerShell-Script:** `scripts/update_index_weights.ps1`

#### 4.1 Task einrichten

```powershell
# Task Scheduler öffnen
taskschd.msc

# Oder via PowerShell:
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File 'D:\Programmieren\Projekte\Produktiv\Web Development\Stock-Watchlist\scripts\update_index_weights.ps1'"

# Täglich um 18:00 Uhr (nach Börsenschluss US)
$Trigger = New-ScheduledTaskTrigger -Daily -At "18:00"

# Task registrieren
Register-ScheduledTask -TaskName "Stock-Watchlist Weight Update" -Action $Action -Trigger $Trigger -Description "Updates index constituent weights daily"
```

#### 4.2 Script-Parameter

```powershell
# Standard (alle konfigurierten Indices)
.\scripts\update_index_weights.ps1

# Nur bestimmte Indices
.\scripts\update_index_weights.ps1 -Indices @("^GSPC", "^GDAXI")

# Dry-Run
.\scripts\update_index_weights.ps1 -DryRun

# Equal-Weight Methode
.\scripts\update_index_weights.ps1 -Method equal

# Eigene Virtual Environment
.\scripts\update_index_weights.ps1 -VenvPath "C:\custom\path\.venv"
```

#### 4.3 Empfohlene Schedule

| Zeit | Grund |
|------|-------|
| **Täglich 18:00 Uhr** | Nach US-Börsenschluss (NYSE: 16:00 ET = 22:00 CET) |
| **Täglich 22:00 Uhr** | Nach EU-Börsenschluss |
| **Wöchentlich (Sonntag)** | Für weniger kritische Indices |

### Linux/macOS Cron

```bash
# Crontab öffnen
crontab -e

# Täglich um 18:00
0 18 * * * cd /path/to/Stock-Watchlist && /path/to/.venv/bin/python tools/calculate_index_weights.py --index "^GSPC" >> /var/log/weight-update.log 2>&1

# Mehrere Indices nacheinander
0 18 * * * cd /path/to/Stock-Watchlist && /path/to/.venv/bin/python tools/calculate_index_weights.py --index "^GSPC" && /path/to/.venv/bin/python tools/calculate_index_weights.py --index "^GDAXI"
```

## Option 5: Frontend-Integration

### Button in der UI (zukünftig)

Könnte in `IndexDetailPage` integriert werden:

```javascript
const handleRecalculateWeights = async () => {
  try {
    const response = await fetch(
      `/api/v1/indices/${ticker}/constituents/recalculate-weights?method=market_cap`,
      { method: 'POST' }
    );
    const result = await response.json();
    
    if (result.success) {
      toast.success(`Gewichtungen aktualisiert: ${result.updated_count} Constituents`);
      refetchConstituents();
    }
  } catch (error) {
    toast.error('Fehler beim Aktualisieren der Gewichtungen');
  }
};
```

## Zusammenfassung

### Wann wird was genutzt?

| Szenario | Lösung |
|----------|--------|
| **CSV-Import** | Option 1 (automatisch, kein manueller Eingriff nötig) |
| **Einmaliges manuelles Update** | Option 2 (API) oder Option 3 (CLI) |
| **Regelmäßige automatische Updates** | Option 4 (Scheduled Task) - **Empfohlen!** |
| **On-Demand via UI** | Option 5 (Frontend-Button) |

### Empfohlenes Setup

1. **CSV-Import:** `auto_calculate_weights=true` (Standard) - keine manuelle Gewichtung nötig
2. **Scheduled Task:** Täglich 18:00 Uhr für wichtige Indices (S&P 500, DAX, Nasdaq-100)
3. **API-Endpoint:** Für manuelle Ad-hoc Updates bei Bedarf

### Vorteile der Automatisierung

✅ **Keine manuelle Wartung** - Gewichtungen bleiben immer aktuell  
✅ **Echtzeitdaten** - Basiert auf aktuellen Market Caps von yfinance  
✅ **Konsistenz** - Keine veralteten CSV-Daten  
✅ **Flexibilität** - Verschiedene Methoden (Market Cap, Equal Weight)  
✅ **Audit Trail** - Logs zeigen Änderungen und Zeitpunkte

## Monitoring

### Log-Output prüfen

```powershell
# PowerShell Script Logs
Get-Content "D:\Programmieren\Projekte\Produktiv\Web Development\Stock-Watchlist\logs\weight-updates.log" -Tail 50

# Python CLI Logs
python tools/calculate_index_weights.py --index "^GSPC" --dry-run
```

### Letzte Updates prüfen

```sql
-- SQL Query für letzte Änderungen
SELECT 
    ic.updated_at,
    mi.name,
    s.ticker_symbol,
    ic.weight
FROM index_constituents ic
JOIN market_indices mi ON ic.index_id = mi.id
JOIN stocks s ON ic.stock_id = s.id
WHERE mi.ticker_symbol = '^GSPC'
ORDER BY ic.updated_at DESC
LIMIT 10;
```

## Troubleshooting

### Problem: Weight-Calculation schlägt fehl

**Lösung:** Market-Cap-Daten prüfen
```bash
python tools/calculate_index_weights.py --index "^GSPC" --dry-run
```

### Problem: Scheduled Task läuft nicht

**Lösung:** Task Scheduler Logs prüfen
```powershell
Get-ScheduledTask -TaskName "Stock-Watchlist Weight Update" | Get-ScheduledTaskInfo
```

### Problem: Virtuelle Umgebung nicht gefunden

**Lösung:** Pfad im Script anpassen
```powershell
.\scripts\update_index_weights.ps1 -VenvPath "C:\eigener\pfad\.venv"
```
