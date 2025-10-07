# 📊 Technical Indicators Implementation Guide

## Übersicht

Dieses Dokument beschreibt die Implementierung der technischen Indikatoren für Swing-Trading und langfristiges Investieren.

---

## 🎯 Indikator-Liste

### **Bereits Implementiert** ✅

| Indikator | Backend | Frontend Chart | Calculated Metrics | Status |
|-----------|---------|----------------|-------------------|--------|
| **SMA 50** | ✅ | ✅ | ✅ | Komplett |
| **SMA 200** | ✅ | ✅ | ✅ | Komplett |
| **RSI (14)** | ✅ | ✅ | ✅ | Komplett |
| **MACD** | ✅ | ✅ | ✅ | Komplett |
| **Bollinger Bands** | ✅ | ✅ | ❌ | **NEU** |
| **Volume** | ✅ | ✅ | ✅ | Komplett |
| **Volatility** | ✅ | ❌ | ✅ | Nur Wert |

### **In Arbeit** 🚧

| Indikator | Backend | Frontend Chart | Calculated Metrics | Status |
|-----------|---------|----------------|-------------------|--------|
| **VWAP (Rolling 20)** | ⏳ | ⏳ | ⏳ | Phase 3 |
| **Golden Cross Badge** | ✅ | ⏳ | ⏳ | Phase 4 |
| **Death Cross Badge** | ✅ | ⏳ | ⏳ | Phase 4 |

### **Abgeschlossen** ✅

| Indikator | Completion Date |
|-----------|----------------|
| **Bollinger Bands Visualization** | October 7, 2025 |
| **ATR (14) Full Implementation** | October 7, 2025 |

---

## 📋 Phase 1: Bollinger Bands ✅ FERTIG

### Backend
- **Datei**: `backend/app/services/yfinance_service.py`
- **Funktion**: `calculate_technical_indicators()`
- **Indikator-Parameter**: `'bollinger'`
- **Berechnung**: 
  - Middle Band: SMA(20)
  - Upper Band: SMA(20) + 2*STD(20)
  - Lower Band: SMA(20) - 2*STD(20)

### Frontend
- **Datei**: `frontend/src/components/StockChart.js`
- **Toggle**: `showBollinger` State
- **Visualisierung**:
  - Oberes Band: Rote gestrichelte Linie (#e74c3c)
  - Unteres Band: Grüne gestrichelte Linie (#27ae60)
  - Mittleres Band: Graue gestrichelte Linie (#95a5a6)
  - Fläche zwischen Bändern: Semi-transparent (10% Opacity)
- **Tooltip**: Zeigt alle drei Werte an

### Verwendung
```javascript
// Toggle Bollinger Bands im Chart
<label className="checkbox-label">
  <input
    type="checkbox"
    checked={showBollinger}
    onChange={(e) => setShowBollinger(e.target.checked)}
  />
  <span>Bollinger Bands</span>
</label>
```

---

## 📋 Phase 2: ATR (Average True Range) ✅ FERTIG
**Completion Date**: October 7, 2025  
**Status**: Fully implemented and tested - all 251 data points rendering correctly

**Bug Fixed**: 
- f-string format specifier error in `_calculate_atr_series` logging statement
- Issue: `ValueError: Invalid format specifier` when using ternary operator with format specifier
- Solution: Split format operation into separate variable before logging

**Test Results**:
- ✅ Backend calculation working (True Range → EWM smoothing)
- ✅ API endpoint returning ATR data (251 values)
- ✅ Frontend receiving and transforming data correctly
- ✅ Chart visualization displaying ATR line (Range: 0.78 - 2.13 for NTR 1y)
- ✅ Metrics tab showing Stop-Loss/Take-Profit levels

### Backend - calculated_metrics_service.py ✅

**Datei**: `backend/app/services/calculated_metrics_service.py` (Zeilen 507-603)

**Funktion**: `calculate_atr()`

**Features**:
- Berechnet True Range aus High, Low, Close
- ATR als EMA von True Range (Period: 14)
- ATR als Prozentsatz vom aktuellen Preis
- Stop-Loss Levels: 1.5x, 2x, 3x ATR
- Take-Profit Levels: 2x, 3x, 4x ATR
- Risk/Reward Ratio Berechnung
- Volatility Rating: low, moderate, high, very_high

**Integration**:
- ✅ In `calculate_all_metrics()` integriert (Phase 3)
- ✅ Wird mit historischen Daten berechnet

### Backend - yfinance_service.py ✅

**Datei**: `backend/app/services/yfinance_service.py` (Zeilen 863-889)

**Funktion**: `_calculate_atr_series()`

**Features**:
- ATR als Zeitreihe für Chart-Visualisierung
- Verwendet pandas EWM für glatte Berechnung
- Wird bei `'atr'` oder `'atr_14'` Indikator abgerufen

### Frontend - StockChart.js ✅

**Datei**: `frontend/src/components/StockChart.js`

**Features**:
- ✅ Toggle: `showATR` State
- ✅ Separater ATR-Chart unter Hauptchart (200px Höhe)
- ✅ Orange Linie mit Gradient-Füllung (#f39c12)
- ✅ Info-Box mit Interpretation
- ✅ Tooltip zeigt ATR-Wert

**Visualisierung**:
```jsx
<LineChart data={chartData}>
  <Area
    dataKey="atr"
    stroke="#f39c12"
    fill="url(#atrGradient)"
    name="ATR (14)"
  />
</LineChart>
```

### Frontend - CalculatedMetricsTab.js ✅

**Datei**: `frontend/src/components/CalculatedMetricsTab.js` (Zeilen 469-586)

**Features**:
- ✅ ATR-Wert mit Prozentsatz
- ✅ Volatility Rating Badge
- ✅ 3 Stop-Loss Levels (Conservative, Standard, Aggressive)
- ✅ 3 Take-Profit Levels
- ✅ Risk/Reward Ratio Anzeige
- ✅ Farbcodierung für bessere Lesbarkeit

**Darstellung**:
- Stop-Loss Levels: Gelb 🟡, Orange 🟠, Rot 🔴
- Take-Profit Levels: Hellgrün bis Dunkelgrün
- Separate Boxen mit Hintergrundfarben

### API Response
```json
{
  "phase3_advanced_analysis": {
    "atr_current": 3.45,
    "atr_percentage": 2.3,
    "stop_loss_conservative": 147.83,
    "stop_loss_standard": 146.10,
    "stop_loss_aggressive": 143.65,
    "take_profit_conservative": 156.90,
    "take_profit_standard": 159.35,
    "take_profit_aggressive": 161.80,
    "risk_reward_ratio": 1.5,
    "volatility_rating": "moderate"
  }
}
```

---

## 📋 Phase 3: VWAP (Volume Weighted Average Price) ⏳ NEXT

### Geplante Implementierung

#### Backend - calculated_metrics_service.py
```python
def calculate_vwap_rolling(close_prices: pd.Series,
                          high_prices: pd.Series,
                          low_prices: pd.Series,
                          volume: pd.Series,
                          period: int = 20) -> Dict[str, Any]:
    """
    Berechnet Rolling VWAP (nicht Intraday)
    
    Args:
        close_prices: Close prices
        high_prices: High prices
        low_prices: Low prices
        volume: Volume
        period: Rolling window (default: 20)
        
    Returns:
        Dict mit:
        - vwap_current: Aktueller VWAP
        - vwap_series: VWAP-Zeitreihe
        - price_vs_vwap: 'above' oder 'below'
        - distance_from_vwap: Distanz in %
        - signal: 'bullish', 'bearish', 'neutral'
    """
    result = {
        'vwap_current': None,
        'vwap_series': None,
        'price_vs_vwap': None,
        'distance_from_vwap': None,
        'signal': None
    }
    
    if len(close_prices) < period:
        return result
    
    try:
        # Typical Price = (High + Low + Close) / 3
        typical_price = (high_prices + low_prices + close_prices) / 3
        
        # VWAP = Rolling Sum(Typical Price * Volume) / Rolling Sum(Volume)
        vwap = (typical_price * volume).rolling(window=period).sum() / volume.rolling(window=period).sum()
        
        result['vwap_current'] = float(vwap.iloc[-1])
        result['vwap_series'] = vwap.tolist()
        
        current_price = close_prices.iloc[-1]
        current_vwap = result['vwap_current']
        
        # Price vs VWAP
        if current_price > current_vwap:
            result['price_vs_vwap'] = 'above'
            result['signal'] = 'bullish'
        elif current_price < current_vwap:
            result['price_vs_vwap'] = 'below'
            result['signal'] = 'bearish'
        else:
            result['price_vs_vwap'] = 'at'
            result['signal'] = 'neutral'
        
        # Distance from VWAP
        result['distance_from_vwap'] = ((current_price - current_vwap) / current_vwap) * 100
        
    except Exception as e:
        logger.error(f"Error calculating VWAP: {e}")
    
    return result
```

#### Frontend - StockChart.js
- **Toggle**: `showVWAP` State
- **Darstellung**: Als dicke blaue Linie im Hauptchart
- **Color**: #3498db (Blau)

#### Frontend - CalculatedMetricsTab.js (Phase 1)
```jsx
<div className="indicator-row">
  <div className="indicator-label">
    <MetricTooltip
      title="VWAP (20)"
      description="Volume Weighted Average Price - Institutioneller Durchschnittspreis"
    >
      <span>VWAP</span>
    </MetricTooltip>
  </div>
  <div className="indicator-value">
    {formatCurrency(phase1.vwap_current)}
    {phase1.price_vs_vwap && (
      <span className={`metric-badge-small ${phase1.price_vs_vwap === 'above' ? 'bullish' : 'bearish'}`}>
        {phase1.price_vs_vwap === 'above' ? 'Above ↑' : 'Below ↓'}
      </span>
    )}
    <span style={{ marginLeft: '8px', fontSize: '13px', color: '#666' }}>
      ({formatNumber(phase1.distance_from_vwap, 1)}%)
    </span>
  </div>
</div>
```

---

## 📋 Phase 4: Golden Cross / Death Cross Badges & Chart Markers ⏳

### Golden Cross Detection
- **Bedingung**: SMA 50 > SMA 200
- **Signal**: Bullish (Kaufsignal)
- **Farbe**: Grün 🟢

### Death Cross Detection
- **Bedingung**: SMA 50 < SMA 200
- **Signal**: Bearish (Verkaufssignal)
- **Farbe**: Rot 🔴

### Frontend - CalculatedMetricsTab.js
```jsx
{/* SMA Trend Signals */}
<div className="trend-signals-section">
  {phase1.golden_cross && (
    <div className="trend-badge golden-cross">
      🟢 Golden Cross - Bullish Trend
    </div>
  )}
  {phase1.death_cross && (
    <div className="trend-badge death-cross">
      🔴 Death Cross - Bearish Trend
    </div>
  )}
  {phase1.trend && (
    <div className={`trend-badge trend-${phase1.trend}`}>
      Trend: {getTrendLabel(phase1.trend)} {getTrendIcon(phase1.trend)}
    </div>
  )}
</div>
```

### Frontend - StockChart.js (Chart Markers)
```jsx
// Detect crossover points in historical data
const detectCrossovers = (data) => {
  const crossovers = [];
  
  for (let i = 1; i < data.length; i++) {
    const prev = data[i - 1];
    const curr = data[i];
    
    if (!prev.sma50 || !prev.sma200 || !curr.sma50 || !curr.sma200) continue;
    
    // Golden Cross: SMA50 crosses above SMA200
    if (prev.sma50 <= prev.sma200 && curr.sma50 > curr.sma200) {
      crossovers.push({
        index: i,
        date: curr.date,
        type: 'golden',
        price: curr.close
      });
    }
    
    // Death Cross: SMA50 crosses below SMA200
    if (prev.sma50 >= prev.sma200 && curr.sma50 < curr.sma200) {
      crossovers.push({
        index: i,
        date: curr.date,
        type: 'death',
        price: curr.close
      });
    }
  }
  
  return crossovers;
};

// Im Chart rendern:
{showCrossovers && crossoverPoints.map((crossover, idx) => (
  <ReferenceLine
    key={idx}
    x={crossover.date}
    stroke={crossover.type === 'golden' ? '#27ae60' : '#e74c3c'}
    strokeWidth={2}
    label={{
      value: crossover.type === 'golden' ? '⬆ Golden Cross' : '⬇ Death Cross',
      position: 'top',
      fill: crossover.type === 'golden' ? '#27ae60' : '#e74c3c',
      fontSize: 11,
      fontWeight: 'bold'
    }}
  />
))}
```

---

## 🎨 Farb-Schema

| Element | Farbe | Hex Code |
|---------|-------|----------|
| SMA 50 | Orange | #ff7f0e |
| SMA 200 | Lila | #9467bd |
| RSI | Lila | #8e44ad |
| MACD | Blau/Rot | #007bff / #dc3545 |
| Bollinger Upper | Rot | #e74c3c |
| Bollinger Middle | Grau | #95a5a6 |
| Bollinger Lower | Grün | #27ae60 |
| ATR | Orange | #f39c12 |
| VWAP | Blau | #3498db |
| Golden Cross | Grün | #27ae60 |
| Death Cross | Rot | #e74c3c |

---

## 🔄 API Endpoints

### GET /stock-data/{stock_id}/technical-indicators
**Query Parameters:**
- `period`: Zeitraum (1d, 5d, 1mo, 3mo, 6mo, 1y, 3y, 5y, max)
- `indicators`: Array von Indikatoren
  - `sma_50`
  - `sma_200`
  - `rsi`
  - `macd`
  - `bollinger` ✅
  - `atr` (geplant)
  - `vwap` (geplant)

**Response:**
```json
{
  "stock_id": 1,
  "ticker_symbol": "AAPL",
  "period": "1y",
  "dates": ["2024-01-01", "2024-01-02", ...],
  "close": [150.5, 151.2, ...],
  "indicators": {
    "sma_50": [148.2, 148.5, ...],
    "sma_200": [145.0, 145.2, ...],
    "rsi": [65.4, 67.2, ...],
    "macd": {
      "macd": [1.2, 1.5, ...],
      "signal": [1.0, 1.1, ...],
      "histogram": [0.2, 0.4, ...]
    },
    "bollinger": {
      "upper": [155.0, 156.0, ...],
      "middle": [150.0, 151.0, ...],
      "lower": [145.0, 146.0, ...]
    }
  }
}
```

---

## ✅ Testing Checklist

### Phase 1: Bollinger Bands ✅
- [x] Backend berechnet Bollinger Bands korrekt
- [x] Frontend fetcht Bollinger Bands
- [x] Toggle funktioniert
- [x] Visualisierung im Line Chart
- [x] Visualisierung im Candlestick Chart
- [x] Tooltip zeigt alle 3 Werte
- [x] Farben sind korrekt

### Phase 2: ATR ✅
- [x] Backend berechnet ATR korrekt
- [x] Stop-Loss-Levels werden berechnet
- [x] Take-Profit-Levels werden berechnet
- [x] Frontend fetcht ATR
- [x] Toggle funktioniert
- [x] Visualisierung im separaten Chart
- [x] Calculated Metrics zeigt ATR + Stop-Loss + Take-Profit
- [x] Volatility Rating wird angezeigt
- [x] Risk/Reward Ratio wird angezeigt
- [x] Info-Box im Chart mit Interpretationshilfe

### Phase 3: VWAP (TODO)
- [ ] Backend berechnet Rolling VWAP
- [ ] Frontend fetcht VWAP
- [ ] Toggle funktioniert
- [ ] Visualisierung als Linie
- [ ] Calculated Metrics zeigt VWAP
- [ ] Above/Below Badge funktioniert

### Phase 4: Crossover Signals (TODO)
- [ ] Crossover Detection funktioniert
- [ ] Badges in Calculated Metrics
- [ ] Badges im Chart-Header
- [ ] Vertikale Linien im Chart
- [ ] Toggle für Crossover-Marker

---

## 📚 Ressourcen

- [Trading View - Bollinger Bands](https://www.tradingview.com/support/solutions/43000501972-bollinger-bands-bb/)
- [Investopedia - ATR](https://www.investopedia.com/terms/a/atr.asp)
- [Investopedia - VWAP](https://www.investopedia.com/terms/v/vwap.asp)
- [Investopedia - Golden Cross](https://www.investopedia.com/terms/g/goldencross.asp)

---

**Status**: Phase 1 ✅ Fertig | Phase 2 ✅ Fertig | Phase 3-4 🚧 In Arbeit
**Letzte Aktualisierung**: 2025-10-07
