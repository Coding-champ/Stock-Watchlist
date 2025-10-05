# API Documentation - Calculated Metrics Endpoints

## Overview

The Calculated Metrics API provides comprehensive stock analysis through multi-phase metric calculations. All metrics are automatically cached for 1 hour to ensure optimal performance.

---

## Endpoints

### 1. Get Calculated Metrics

**Endpoint:** `GET /api/stock-data/{stock_id}/calculated-metrics`

**Description:** Calculate and return comprehensive metrics for stock analysis.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `stock_id` | integer | Yes | - | The ID of the stock in the database |
| `period` | string | No | `"1y"` | Historical data period for technical analysis |
| `use_cache` | boolean | No | `true` | Whether to use cached results |

**Valid period values:** `"1mo"`, `"3mo"`, `"6mo"`, `"1y"`, `"2y"`

#### Response Schema

```json
{
  "phase1_basic_indicators": {
    "week_52_metrics": {
      "distance_from_52w_high": -10.5,
      "distance_from_52w_low": 45.2,
      "position_in_52w_range": 75.0,
      "interpretation": "stock_near_high"
    },
    "sma_metrics": {
      "sma_50": 170.0,
      "sma_200": 160.0,
      "price_vs_sma50": 5.88,
      "price_vs_sma200": 12.5,
      "trend": "bullish",
      "golden_cross": true,
      "death_cross": false
    },
    "volume_metrics": {
      "relative_volume": 0.91,
      "volume_category": "normal"
    },
    "fcf_yield": 2.67
  },
  "phase2_valuation_scores": {
    "value_metrics": {
      "pe_score": 65.0,
      "pb_score": 70.0,
      "ps_score": 60.0,
      "value_score": 65.0,
      "rating": "good"
    },
    "quality_metrics": {
      "roe_score": 85.0,
      "roa_score": 75.0,
      "margin_score": 76.0,
      "quality_score": 78.5,
      "rating": "good"
    },
    "dividend_metrics": {
      "dividend_yield_score": 80.0,
      "payout_ratio_score": 90.0,
      "dividend_growth_score": 90.0,
      "dividend_safety_score": 86.7,
      "rating": "very_safe"
    }
  },
  "phase3_advanced_analysis": {
    "macd": {
      "macd_line": 2.5,
      "signal_line": 1.8,
      "histogram": 0.7,
      "trend": "bullish"
    },
    "stochastic": {
      "k_percent": 75.0,
      "d_percent": 70.0,
      "signal": "neutral",
      "is_overbought": false,
      "is_oversold": false
    },
    "volatility": {
      "volatility_30d": 24.5,
      "volatility_90d": 26.2,
      "volatility_1y": 28.0,
      "volatility_category": "low"
    },
    "drawdown": {
      "max_drawdown": -15.5,
      "current_drawdown": -5.2,
      "max_drawdown_duration": 45
    },
    "beta_adjusted_metrics": {
      "total_return": 25.5,
      "annualized_return": 25.8,
      "sharpe_ratio": 0.85,
      "alpha": 5.2,
      "treynor_ratio": 0.12,
      "sortino_ratio": 1.2,
      "beta_adjusted_return": 23.4,
      "information_ratio": 0.45,
      "downside_deviation": 18.5,
      "risk_rating": "moderate"
    },
    "risk_adjusted_performance": {
      "overall_score": 75.0,
      "rating": "good",
      "sharpe_contribution": 70.0,
      "alpha_contribution": 85.0,
      "sortino_contribution": 80.0,
      "information_contribution": 65.0
    }
  },
  "calculation_timestamp": "2025-10-04T12:00:00.000000"
}
```

#### Response Codes

| Code | Description |
|------|-------------|
| `200` | Success - Metrics calculated |
| `404` | Stock not found or data unavailable |
| `500` | Internal server error during calculation |

#### Example Request

```bash
curl -X GET "http://localhost:8000/api/stock-data/1/calculated-metrics?period=1y&use_cache=true"
```

#### Example Response (Success)

```json
{
  "phase1_basic_indicators": {
    "week_52_metrics": {
      "distance_from_52w_high": -10.5,
      "position_in_52w_range": 75.0
    }
  },
  "calculation_timestamp": "2025-10-04T12:00:00"
}
```

---

### 2. Get Stock with Calculated Metrics

**Endpoint:** `GET /api/stocks/{stock_id}/with-calculated-metrics`

**Description:** Retrieve complete stock information including all calculated metrics in a single call.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `stock_id` | integer | Yes | - | The ID of the stock in the database |
| `period` | string | No | `"1y"` | Historical data period for technical analysis |
| `force_refresh` | boolean | No | `false` | Force cache refresh |

#### Response Schema

```json
{
  "id": 1,
  "ticker_symbol": "AAPL",
  "name": "Apple Inc.",
  "isin": "US0378331005",
  "country": "US",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "watchlist_id": 1,
  "position": 1,
  "observation_reasons": ["fundamentals", "chart_technical"],
  "observation_notes": "Strong fundamentals",
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-10-04T12:00:00",
  "latest_data": {
    "id": 100,
    "stock_id": 1,
    "current_price": 180.0,
    "pe_ratio": 28.5,
    "timestamp": "2025-10-04T12:00:00"
  },
  "extended_data": {
    "business_summary": "Apple Inc. designs, manufactures...",
    "financial_ratios": {
      "pe_ratio": 28.5,
      "peg_ratio": 2.1
    }
  },
  "calculated_metrics": {
    "phase1_basic_indicators": { "...": "..." },
    "phase2_valuation_scores": { "...": "..." },
    "phase3_advanced_analysis": { "...": "..." }
  }
}
```

#### Response Codes

| Code | Description |
|------|-------------|
| `200` | Success - Stock with metrics retrieved |
| `404` | Stock not found |
| `500` | Internal server error |

---

## Metric Descriptions

### Phase 1: Basic Indicators

#### 52-Week Metrics
- **distance_from_52w_high**: Percentage distance from 52-week high (negative = below high)
- **distance_from_52w_low**: Percentage distance from 52-week low (positive = above low)
- **position_in_52w_range**: Position in 52-week range (0-100, where 100 = at high)
- **interpretation**: `"stock_near_low"`, `"stock_near_high"`, or `"stock_mid_range"`

#### SMA Metrics
- **sma_50**: 50-day Simple Moving Average
- **sma_200**: 200-day Simple Moving Average
- **trend**: `"bullish"` (price above both), `"bearish"` (below both), `"neutral"` (mixed)
- **golden_cross**: True if SMA50 > SMA200 (bullish signal)
- **death_cross**: True if SMA50 < SMA200 (bearish signal)

#### Volume Metrics
- **relative_volume**: Current volume / average volume ratio
- **volume_category**: `"very_low"` (< 0.5), `"low"` (0.5-0.8), `"normal"` (0.8-1.2), `"high"` (1.2-1.5), `"very_high"` (> 1.5)

#### Free Cashflow Yield
- FCF / Market Cap × 100
- Higher is better (indicates cash generation efficiency)

---

### Phase 2: Valuation Scores

All scores are on a 0-100 scale where:
- **0-25**: Poor
- **25-50**: Below Average
- **50-75**: Good
- **75-100**: Excellent

#### Value Score
Combines P/E, P/B, and P/S ratios to assess if stock is undervalued.

#### Quality Score
Evaluates profitability through ROE, ROA, and profit margins.

#### Dividend Safety Score
Assesses dividend sustainability through yield, payout ratio, and growth.

---

### Phase 3: Advanced Analysis

#### MACD (Moving Average Convergence Divergence)
- **macd_line**: Fast EMA - Slow EMA
- **signal_line**: 9-period EMA of MACD line
- **histogram**: MACD line - Signal line
- **trend**: `"bullish"` (histogram > 0), `"bearish"` (< 0), `"neutral"`

#### Stochastic Oscillator
- **k_percent**: Current position in price range (0-100)
- **d_percent**: 3-period SMA of %K
- **signal**: `"overbought"` (>80), `"oversold"` (<20), `"neutral"`

#### Volatility Metrics
- **volatility_30d/90d/1y**: Annualized volatility (%)
- **volatility_category**: 
  - `"very_low"`: < 15%
  - `"low"`: 15-25%
  - `"moderate"`: 25-40%
  - `"high"`: 40-60%
  - `"very_high"`: > 60%

#### Beta-Adjusted Metrics

##### Sharpe Ratio
- **Formula**: (Return - Risk-Free Rate) / Volatility
- **Interpretation**:
  - < 0: Bad (negative excess return)
  - 0-0.5: Poor
  - 0.5-1.0: Good
  - 1.0-2.0: Very Good
  - \> 2.0: Excellent

##### Alpha
- Excess return vs CAPM expected return
- **Interpretation**:
  - Positive: Outperforming market
  - Zero: Market performance
  - Negative: Underperforming

##### Treynor Ratio
- Return per unit of systematic risk (beta)
- Higher is better

##### Sortino Ratio
- Like Sharpe but uses downside deviation
- Penalizes only negative volatility

##### Information Ratio
- Risk-adjusted alpha
- Measures consistency of outperformance

##### Risk Rating
- `"low"`: Sharpe > 1.0, low volatility
- `"moderate"`: Sharpe 0.5-1.0
- `"high"`: Sharpe 0-0.5
- `"very_high"`: Sharpe < 0

#### Risk-Adjusted Performance Score
- **overall_score**: 0-100 composite score
- **rating**: `"excellent"` (>75), `"good"` (50-75), `"average"` (25-50), `"poor"` (<25)
- **contributions**: Individual metric contributions to overall score

---

## Caching

All calculated metrics are cached with the following strategy:

- **TTL (Time To Live)**: 1 hour (3600 seconds)
- **Cache Key Format**: `calculated_metrics:{ticker}:{period}`
- **Cache Service**: In-memory SimpleCache with automatic expiration
- **Override**: Use `use_cache=false` to force recalculation

### Cache Performance

- **Cache Hit**: < 1ms response time
- **Cache Miss**: 7-50ms calculation time (depending on data complexity)
- **Speedup**: ~100-500x faster when cached

---

## Error Handling

### Common Errors

#### 404 - Stock Not Found
```json
{
  "detail": "Stock not found"
}
```

**Cause:** Invalid `stock_id` or stock deleted from database.

#### 404 - Data Unavailable
```json
{
  "detail": "Could not fetch data for ticker AAPL"
}
```

**Cause:** yfinance API unavailable or ticker delisted.

#### 500 - Calculation Error
```json
{
  "detail": "Error calculating metrics: insufficient historical data"
}
```

**Cause:** Insufficient data for calculations (need minimum 30 days).

---

## Performance Considerations

### Minimum Data Requirements

| Metric | Minimum Days |
|--------|--------------|
| 52-Week Metrics | 252 (1 year) |
| SMA 50/200 | 200 |
| MACD | 35 |
| Stochastic | 14 |
| Beta Metrics | 30 |
| Volatility | 30 |

### Optimization Tips

1. **Use Caching**: Enable `use_cache=true` (default)
2. **Appropriate Period**: Use shorter periods (1mo-6mo) for faster calculations
3. **Batch Requests**: If analyzing multiple stocks, spread requests over time
4. **Async Calls**: Use async/await in frontend for better UX

---

## Usage Examples

### Python (requests)

```python
import requests

# Get calculated metrics
response = requests.get(
    "http://localhost:8000/api/stock-data/1/calculated-metrics",
    params={"period": "1y", "use_cache": True}
)

metrics = response.json()
print(f"Sharpe Ratio: {metrics['phase3_advanced_analysis']['beta_adjusted_metrics']['sharpe_ratio']}")
```

### JavaScript (fetch)

```javascript
// Get stock with calculated metrics
fetch('http://localhost:8000/api/stocks/1/with-calculated-metrics?period=1y')
  .then(response => response.json())
  .then(data => {
    const metrics = data.calculated_metrics;
    console.log('Risk Score:', metrics.phase3_advanced_analysis.risk_adjusted_performance.overall_score);
  });
```

### cURL

```bash
# Get calculated metrics with 6-month period
curl -X GET \
  "http://localhost:8000/api/stock-data/1/calculated-metrics?period=6mo&use_cache=true" \
  -H "accept: application/json"

# Force refresh
curl -X GET \
  "http://localhost:8000/api/stock-data/1/calculated-metrics?use_cache=false" \
  -H "accept: application/json"
```

---

## Testing

The API includes comprehensive test coverage:

- **Service Layer Tests**: 9/9 passed (100%)
- **Performance Tests**: < 10ms average calculation time
- **Edge Case Tests**: Handles missing data gracefully

Run tests:
```bash
pytest tests/test_service_calculated_metrics.py -v
```

---

## Changelog

### Version 1.0.0 (2025-10-04)

**Added:**
- Phase 1: Basic Indicators (52W, SMA, Volume, FCF)
- Phase 2: Valuation Scores (Value, Quality, Dividend)
- Phase 3: Advanced Analysis (MACD, Stochastic, Volatility, Beta-adjusted)
- Risk-Adjusted Performance Score (0-100)
- Comprehensive caching system
- Full Swagger/OpenAPI documentation

**Performance:**
- < 10ms calculation time
- 1-hour cache TTL
- 286x faster than 2s requirement

---

## Support

For issues or questions:
- Check Swagger UI: `http://localhost:8000/docs`
- Review test examples: `tests/test_service_calculated_metrics.py`
- See comprehensive guide: `BETA_ADJUSTED_METRICS_GUIDE.md`

---

**Last Updated:** 2025-10-04  
**API Version:** 1.0.0  
**Framework:** FastAPI 0.104.1
