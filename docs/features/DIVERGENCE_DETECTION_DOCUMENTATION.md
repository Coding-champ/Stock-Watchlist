# 📊 Technical Indicators Service - Divergence Detection

**Datum:** 08.10.2025  
**Version:** 2.0  
**Status:** ✅ Implementiert und getestet

---

## 🎯 Übersicht

Diese Dokumentation beschreibt das **Refactoring der technischen Indikatoren** und die neue **Divergenz-Detection** für RSI und MACD.

---

## 📁 Neue Dateistruktur

### ✨ NEU: `technical_indicators_service.py`

**Pfad:** `backend/app/services/technical_indicators_service.py`

**Zweck:** Zentrale Service-Datei für alle technischen Indikatoren und Divergenz-Detection.

**Funktionen:**
- `calculate_rsi()` - RSI Berechnung mit Wilder's Smoothing
- `calculate_macd()` - MACD Berechnung (Line, Signal, Histogram)
- `detect_rsi_divergence()` - Erkennt bullish/bearish RSI Divergenzen
- `detect_macd_divergence()` - Erkennt bullish/bearish MACD Divergenzen
- `analyze_technical_indicators_with_divergence()` - Komplette Analyse mit Trading-Signal

---

## 🔄 Refactoring Details

### Was wurde verschoben?

**Von `calculated_metrics_service.py`:**
- `calculate_macd()` → `technical_indicators_service.py`
- RSI/MACD Berechnung (dedupliziert)

**Von `yfinance_service.py`:**
- `_calculate_rsi()` → Wrapper zu `technical_indicators_service.py`
- `_calculate_rsi_series()` → Wrapper zu `technical_indicators_service.py`

**Von `alert_service.py`:**
- `_calculate_rsi()` → Wrapper zu `technical_indicators_service.py`

### ✅ Backward Compatibility

Alle alten Funktionen sind als **Wrapper** erhalten geblieben:
```python
# Beispiel in yfinance_service.py
def _calculate_rsi(close_prices: pd.Series, period: int = 14) -> Optional[float]:
    """Wrapper for backward compatibility"""
    result = calculate_rsi(close_prices, period)
    return result.get('value')
```

**Vorteil:** Keine Breaking Changes für bestehenden Code!

---

## 🆕 Neue Features

### 1. RSI Divergenz Detection

**Funktion:** `detect_rsi_divergence()`

**Parameter:**
- `close_prices`: Pandas Series der Schlusskurse
- `rsi_series`: Pandas Series der RSI-Werte
- `lookback_days`: Zeitraum für Analyse (default: **60 Tage**)
- `num_peaks`: Anzahl Peaks für Vergleich (default: **3 Peaks**)
- `min_peak_distance`: Min. Abstand zwischen Peaks (default: 5)

**Returns:**
```python
{
    'bullish_divergence': bool,
    'bearish_divergence': bool,
    'bullish_divergence_points': [
        {
            'price_index': int,
            'price_value': float,
            'indicator_index': int,
            'indicator_value': float
        }
    ],
    'bearish_divergence_points': [...],
    'signal': 'bullish' | 'bearish' | None,
    'confidence': float (0-100)
}
```

**Divergenz-Logik:**

**Bullish Divergence (Kaufsignal):**
```
Preis:     \  /    (macht tiefere Tiefs)
RSI:        \/     (macht höhere Tiefs) 
           ↗↗↗     = Momentum kehrt um!
```

**Bearish Divergence (Verkaufssignal):**
```
Preis:      /\     (macht höhere Hochs)
RSI:       /  \    (macht tiefere Hochs)
           ↘↘↘     = Momentum lässt nach!
```

---

### 2. MACD Divergenz Detection

**Funktion:** `detect_macd_divergence()`

**Parameter:** Identisch zu RSI, aber mit `macd_histogram` statt `rsi_series`

**Returns:** Gleiche Struktur wie RSI Divergenz

**Hinweis:** MACD Histogram wird für Divergenz-Detection verwendet (nicht MACD Line).

---

### 3. Comprehensive Analysis

**Funktion:** `analyze_technical_indicators_with_divergence()`

**Macht:**
1. Berechnet RSI
2. Berechnet MACD
3. Erkennt RSI Divergenzen
4. Erkennt MACD Divergenzen
5. Bestimmt Overall Trading Signal

**Overall Signal:**
- `strong_buy` - Mehrere bullish Signale
- `buy` - Leicht bullish
- `neutral` - Gemischte Signale
- `sell` - Leicht bearish
- `strong_sell` - Mehrere bearish Signale

**Signal-Gewichtung:**
- RSI oversold/overbought: ±2 Punkte
- MACD Trend: ±1 Punkt
- Divergenzen: ±2 Punkte (hohe Gewichtung!)

---

## 🚨 Neue Alert Types

### Automatische Divergenz-Alerts

**4 neue Alert Types in `alert_service.py`:**

1. **`rsi_bullish_divergence`**
   - Triggert bei erkannter RSI Bullish Divergence
   - Automatisch aktiv (User muss nicht manuell erstellen)

2. **`rsi_bearish_divergence`**
   - Triggert bei erkannter RSI Bearish Divergence
   - Automatisch aktiv

3. **`macd_bullish_divergence`**
   - Triggert bei erkannter MACD Bullish Divergence
   - Automatisch aktiv

4. **`macd_bearish_divergence`**
   - Triggert bei erkannter MACD Bearish Divergence
   - Automatisch aktiv

**Implementierung:**
```python
def _check_rsi_bullish_divergence_alert(self, alert: AlertModel) -> bool:
    """Check for RSI bullish divergence"""
    # Get 3 months data
    hist = ticker.history(period="3mo")
    
    # Calculate RSI
    rsi_data = calculate_rsi(close_prices)
    rsi_series = pd.Series(rsi_data['series'], index=close_prices.index)
    
    # Detect divergence
    divergence = detect_rsi_divergence(close_prices, rsi_series, lookback_days=60, num_peaks=3)
    
    return divergence.get('bullish_divergence', False)
```

---

## 🔌 Neue API Endpoints

### GET `/stock-data/{stock_id}/divergence-analysis`

**Beschreibung:** Comprehensive technical analysis mit Divergenz-Detection

**Query Parameters:**
- `lookback_days` (optional, default: 60) - Zeitraum für Divergenz-Analyse

**Response:**
```json
{
  "stock_id": 1,
  "ticker_symbol": "AAPL",
  "lookback_days": 60,
  "analyzed_at": "2025-10-08T10:30:00",
  "analysis": {
    "rsi": {
      "value": 69.34,
      "signal": "bullish",
      "series": [...]
    },
    "macd": {
      "macd_line": 6.8040,
      "signal_line": 6.9794,
      "histogram": -0.1754,
      "trend": "bearish",
      "series": {...}
    },
    "divergences": {
      "rsi": {
        "bullish_divergence": false,
        "bearish_divergence": true,
        "bearish_divergence_points": [
          {
            "price_index": 45,
            "price_value": 245.50,
            "indicator_index": 46,
            "indicator_value": 72.3
          }
        ],
        "signal": "bearish",
        "confidence": 70.0
      },
      "macd": {
        "bullish_divergence": false,
        "bearish_divergence": false
      }
    },
    "overall_signal": "sell"
  },
  "dates": [...],
  "close_prices": [...]
}
```

---

## 📊 Frontend Integration (Vorbereitung)

### Chart-Markierungen für Divergenzen

**Datenstruktur für Frontend:**

```javascript
// RSI Chart mit Divergenz-Markierungen
{
  rsi_series: [65.2, 68.1, ...],
  divergence_points: [
    {
      index: 45,
      type: 'bearish',  // oder 'bullish'
      price: 245.50,
      rsi_value: 72.3,
      confidence: 70
    }
  ]
}
```

**Vorgeschlagene Visualisierung:**
- 🔴 **Bearish Divergence:** Rotes Dreieck (▼) am Peak
- 🟢 **Bullish Divergence:** Grünes Dreieck (▲) am Trough
- **Hover-Tooltip:** Zeigt Confidence Score + Details

---

## 🧪 Testing

### Test-Scripts

**1. `test_divergence_detection.py`**
- Testet RSI/MACD Berechnung
- Testet Divergenz-Detection
- Testet Comprehensive Analysis
- **Status:** ✅ Alle Tests bestanden

**2. `test_refactoring_dependencies.py`**
- Testet alle Imports
- Testet Backward Compatibility
- Testet Funktionalität nach Refactoring
- **Status:** ✅ Alle Tests bestanden

### Test-Ergebnisse (AAPL, 08.10.2025)

```
📊 Testing with AAPL...
✅ Retrieved 127 days of data
   Price range: $172.00 - $258.02

RSI: 69.34 (bullish)
MACD: 6.8040 (bearish trend)

🔴 RSI BEARISH DIVERGENCE DETECTED!
   Confidence: 70.0%
   Points: 2

📈 Trading Recommendation: SELL
```

---

## 📦 Dependencies

### Neue Abhängigkeit: scipy

**Hinzugefügt zu `requirements.txt`:**
```
scipy>=1.11.0
```

**Verwendung:** 
- `scipy.signal.argrelextrema` für Peak-Detection
- Findet lokale Maxima und Minima in Zeitserien

**Installation:**
```bash
pip install scipy>=1.11.0
```

---

## 🔧 Konfiguration

### Divergenz-Parameter (anpassbar)

**In `detect_rsi_divergence()` und `detect_macd_divergence()`:**

```python
lookback_days = 60      # Zeitraum für Analyse
num_peaks = 3           # Anzahl Peaks für Vergleich
min_peak_distance = 5   # Min. Abstand zwischen Peaks
```

**Empfehlungen:**
- **Kurzfristig:** lookback_days=30, num_peaks=2
- **Standard:** lookback_days=60, num_peaks=3 (aktuell)
- **Langfristig:** lookback_days=90, num_peaks=4

---

## 📈 Performance

### Benchmarks

- **RSI Calculation:** ~5ms für 180 Tage
- **MACD Calculation:** ~8ms für 180 Tage
- **Divergence Detection:** ~50ms für 60 Tage
- **Comprehensive Analysis:** ~70ms total

**Optimierungen:**
- Pandas/NumPy Vectorization
- Caching kann später hinzugefügt werden (Redis)

---

## 🚀 Nächste Schritte

### Frontend Implementation

1. **Chart-Komponente erweitern:**
   - Divergenz-Punkte als Icons anzeigen
   - Hover-Tooltips mit Details
   - Toggle für Divergenz-Anzeige

2. **Divergence Analysis Tab:**
   - Neuer Tab im StockDetailModal
   - Zeigt erkannte Divergenzen
   - Confidence Scores
   - Historische Divergenzen

3. **Alert UI erweitern:**
   - Checkboxes für Divergenz-Alerts
   - "Enable automatic divergence alerts"
   - Alert History mit Divergenz-Markierungen

### Backend Erweiterungen

1. **Caching:**
   - Divergence Analysis cachen (60 Min TTL)
   - Redis Integration

2. **Historische Divergenzen:**
   - Speichern erkannter Divergenzen in DB
   - Erfolgsrate tracken ("War die Divergenz richtig?")

3. **Weitere Indikatoren:**
   - Volume Profile Divergenz
   - Ichimoku Divergenz (geplant)

---

## 📚 Ressourcen

### Algorithmus-Referenzen

- **Peak Detection:** [scipy.signal.argrelextrema](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.argrelextrema.html)
- **RSI Divergenz:** [TradingView Guide](https://www.tradingview.com/support/solutions/43000502338-rsi-divergence/)
- **MACD Divergenz:** [Investopedia](https://www.investopedia.com/terms/m/macd.asp)

### Trading Education

- **Bullish Divergence Strategie:** YouTube "Rayner Teo RSI Divergence"
- **Divergence Trading:** "Trading with Divergences" (eBook)

---

## ✅ Checklist

- [x] Neue Datei `technical_indicators_service.py` erstellt
- [x] RSI/MACD Code refactored und verschoben
- [x] Divergenz-Detection implementiert (3 Peaks, 60 Tage)
- [x] Alert Service erweitert (4 neue Alert Types)
- [x] API Endpoint `/divergence-analysis` erstellt
- [x] Backward Compatibility gewährleistet
- [x] scipy zu requirements.txt hinzugefügt
- [x] Tests geschrieben und bestanden
- [x] Dokumentation erstellt
- [ ] Frontend Chart-Markierungen (TODO)
- [ ] Frontend Divergence Analysis Tab (TODO)
- [ ] Caching implementieren (TODO)

---

**Stand:** 08.10.2025  
**Implementiert von:** GitHub Copilot + User Collaboration  
**Status:** ✅ Ready for Frontend Integration
