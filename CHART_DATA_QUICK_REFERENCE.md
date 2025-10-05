# 📊 Chart-Daten Quick Reference

## 🎯 Übersicht

yfinance kann **ALLE** benötigten Chart-Daten für dein Stock-Watchlist-Projekt liefern!

## ✅ Verfügbare Daten

### 1. **OHLCV-Daten** (Open, High, Low, Close, Volume)
- ✅ Tägliche Daten bis zu 10+ Jahre zurück
- ✅ Intraday-Daten (1m, 5m, 15m, 30m, 1h) bis zu 60 Tage
- ✅ Wöchentliche/Monatliche Daten für Langzeit-Charts

### 2. **Dividenden & Splits**
- ✅ Komplette Dividendenhistorie
- ✅ Stock Split Historie
- ✅ Automatisch in Chart-Daten enthalten

### 3. **Technische Indikatoren**
- ✅ Moving Averages (SMA, EMA)
- ✅ RSI (Relative Strength Index)
- ✅ MACD (Moving Average Convergence Divergence)
- ✅ Bollinger Bands
- ✅ Volatilität

---

## 🚀 Schnellstart

### API Endpunkte

```
GET /stock-data/{stock_id}/chart
    ?period=1y
    &interval=1d
    &include_dividends=true
    &include_volume=true

GET /stock-data/{stock_id}/chart/intraday
    ?days=5

GET /stock-data/{stock_id}/technical-indicators
    ?period=1y
    &indicators=sma_20
    &indicators=rsi
```

---

## 📈 Verwendung für Metriken

Die Chart-Daten können für VIELE Metriken verwendet werden:

### Verfügbare Metriken aus Chart-Daten

| Metrik | Berechnung aus Chart-Daten | Zeitraum |
|--------|---------------------------|----------|
| **Volatilität** | Standardabweichung der Returns | 30/90/365 Tage |
| **Beta** | Korrelation mit Marktindex (S&P 500) | 1-3 Jahre |
| **Sharpe Ratio** | (Return - Risk-free) / Volatilität | 1-3 Jahre |
| **Maximum Drawdown** | Größter Peak-to-Trough Verlust | 1-5 Jahre |
| **RSI** | Relative Strength Index | 14 Tage |
| **MACD** | Moving Average Convergence | 12/26 Tage |
| **52-Week High/Low** | Min/Max der letzten 252 Tage | 1 Jahr |
| **Average Volume** | Durchschnittliches Handelsvolumen | 30/90 Tage |
| **Price Momentum** | Prozentuale Preisänderung | 1/3/6/12 Monate |
| **Moving Averages** | SMA/EMA für Trend-Analyse | 20/50/200 Tage |
| **Support/Resistance** | Lokale Min/Max-Levels | Variable |
| **Bollinger Bands** | Volatilitäts-Bänder | 20 Tage |

### Beispiel: Volatilitäts-Berechnung

```python
import numpy as np
from backend.app.services.yfinance_service import get_chart_data

# Chart-Daten abrufen
chart_data = get_chart_data("AAPL", period="1y", interval="1d")
close_prices = np.array(chart_data['close'])

# Returns berechnen
returns = np.diff(close_prices) / close_prices[:-1]

# Volatilität (annualisiert)
volatility = np.std(returns) * np.sqrt(252) * 100  # in %

print(f"30-Day Volatility: {volatility:.2f}%")
```

### Beispiel: Beta-Berechnung

```python
# Aktien-Daten
stock_data = get_chart_data("AAPL", period="1y", interval="1d")
stock_returns = np.diff(stock_data['close']) / stock_data['close'][:-1]

# Markt-Daten (S&P 500)
market_data = get_chart_data("^GSPC", period="1y", interval="1d")
market_returns = np.diff(market_data['close']) / market_data['close'][:-1]

# Beta berechnen
covariance = np.cov(stock_returns, market_returns)[0, 1]
market_variance = np.var(market_returns)
beta = covariance / market_variance

print(f"Beta: {beta:.2f}")
```

### Beispiel: Sharpe Ratio

```python
# Returns berechnen
returns = np.diff(close_prices) / close_prices[:-1]

# Sharpe Ratio
risk_free_rate = 0.04  # 4% jährlich
excess_returns = returns - (risk_free_rate / 252)
sharpe_ratio = np.mean(excess_returns) / np.std(returns) * np.sqrt(252)

print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
```

---

## 🎨 Frontend Chart-Beispiel

### Simple Price Chart (React + Chart.js)

---

## 📊 Zeiträume & Intervalle

### Empfohlene Kombinationen

| Use Case | Period | Interval | Datenpunkte |
|----------|--------|----------|-------------|
| **Intraday Trading** | 1d | 5m | ~78 |
| **Day Trading** | 5d | 15m | ~130 |
| **Swing Trading** | 1mo | 1h | ~156 |
| **Short-term Analysis** | 3mo | 1d | ~63 |
| **Medium-term Analysis** | 1y | 1d | ~252 |
| **Long-term Analysis** | 5y | 1wk | ~260 |
| **Historical Overview** | max | 1mo | Variable |

### Wichtige Limits

⚠️ **Intraday-Daten sind begrenzt:**

- `1m`, `2m`, `5m`: Maximal 7 Tage
- `15m`, `30m`: Maximal 60 Tage
- `60m`, `90m`, `1h`: Maximal 730 Tage

---

## 💾 Datenformat

### Chart Data Response

```json
{
  "dates": ["2024-01-01T00:00:00", ...],
  "open": [150.25, ...],
  "high": [152.80, ...],
  "low": [149.90, ...],
  "close": [151.50, ...],
  "volume": [75000000, ...],
  "dividends": [
    {"date": "2024-02-15T00:00:00", "amount": 0.24}
  ],
  "splits": [
    {"date": "2024-06-01T00:00:00", "ratio": 4.0}
  ],
  "metadata": {
    "symbol": "AAPL",
    "period": "1y",
    "interval": "1d",
    "data_points": 252
  }
}
```

### Technical Indicators Response

```json
{
  "dates": ["2024-01-01T00:00:00", ...],
  "close": [151.50, ...],
  "indicators": {
    "sma_20": [150.25, ...],
    "sma_50": [148.90, ...],
    "rsi": [65.5, ...],
    "macd": {
      "macd": [1.45, ...],
      "signal": [1.20, ...],
      "histogram": [0.25, ...]
    },
    "bollinger": {
      "upper": [155.30, ...],
      "middle": [150.25, ...],
      "lower": [145.20, ...]
    }
  }
}
```
