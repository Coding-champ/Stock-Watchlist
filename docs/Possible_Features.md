# Feature Gap Analysis: Stock-Watchlist vs. Major Financial Websites

**Analysis Date:** December 31, 2025  
**Websites Analyzed:** Barchart, CNBC, Onvista, MarketBeat, Google Finance, Finviz  
**Purpose:** Identify features, data points, and visualizations not yet implemented in our Stock-Watchlist project

---

## Executive Summary

After analyzing 6 major financial websites and comparing them against our current implementation, I've identified **100+ potential enhancements** across 10 categories. Many data points are available via yfinance, while others would require additional data sources.

### Priority Legend
- 🟢 **Available via yfinance** - Can implement with existing data source
- 🟡 **Partially available** - Some data via yfinance, may need calculations
- 🔴 **Requires new data source** - Need additional API or web scraping
- ⭐ **High Value** - Significant user value / competitive feature

---

## 1. Fundamental Data & Valuation Metrics

### Currently Implemented ✅
- P/E Ratio, P/B Ratio, P/S Ratio
- EPS, Revenue, Net Income
- Market Cap, Shares Outstanding
- ROE, ROA, Debt/Equity
- Dividend Yield, Dividend Rate

### Missing Data Points

| Metric | Source | Availability | Priority |
|--------|--------|--------------|----------|
| **Forward P/E** | Finviz, Barchart | 🟢 yfinance (`forwardPE`) | ⭐ High |
| **PEG Ratio** | Finviz, Onvista | 🟢 yfinance (`pegRatio`) | ⭐ High |
| **EV/EBITDA** | Finviz, Barchart | 🟢 yfinance (`enterpriseToEbitda`) | ⭐ High |
| **EV/Sales** | Finviz | 🟢 yfinance (`enterpriseToRevenue`) | Medium |
| **Enterprise Value** | Finviz | 🟢 yfinance (`enterpriseValue`) | Medium |
| **Price/Cash Flow** | Barchart | 🟢 Can calculate from yfinance | Medium |
| **Price/Free Cash Flow** | Finviz | 🟢 yfinance (`priceToFreeCashFlow`) | ⭐ High |
| **Quick Ratio** | Finviz | 🟢 yfinance (`quickRatio`) | Medium |
| **Current Ratio** | Finviz | 🟢 yfinance (`currentRatio`) | Medium |
| **LT Debt/Equity** | Finviz | 🟡 Calculate from balance sheet | Medium |
| **Gross Margin** | Finviz, CNBC | 🟢 yfinance (`grossMargins`) | Medium |
| **Operating Margin** | Finviz, CNBC | 🟢 yfinance (`operatingMargins`) | Medium |
| **Profit Margin** | Finviz, CNBC | 🟢 yfinance (`profitMargins`) | Medium |
| **ROIC** | Finviz | 🟡 Calculate from financials | ⭐ High |
| **Book Value/Share** | Finviz | 🟢 yfinance (`bookValue`) | Medium |
| **Cash/Share** | Finviz | 🟢 Can calculate | Medium |
| **Revenue per Employee** | Onvista | 🟡 yfinance has employee count | Low |
| **Market Cap/Employee** | Onvista | 🟡 Can calculate | Low |

### Growth Metrics (Missing)

| Metric | Source | Availability | Priority |
|--------|--------|--------------|----------|
| **EPS Growth (YoY)** | Finviz | 🟢 yfinance (`earningsGrowth`) | ⭐ High |
| **EPS Growth (QoQ)** | Finviz | 🟡 Calculate from quarterly | High |
| **Revenue Growth (YoY)** | Finviz | 🟢 yfinance (`revenueGrowth`) | ⭐ High |
| **Revenue Growth (QoQ)** | Finviz | 🟡 Calculate from quarterly | High |
| **EPS Next Year Est.** | Finviz | 🟢 yfinance estimates | ⭐ High |
| **EPS Next 5Y Growth** | Finviz | 🟢 yfinance (`earningsGrowth`) | Medium |
| **Sales Past 5Y Growth** | Finviz | 🟡 Calculate from historical | Medium |

---

## 2. Technical Analysis Enhancements

### Currently Implemented ✅
- RSI, MACD, SMA (50/200), Bollinger Bands
- Stochastic, ATR, VWAP, Ichimoku Cloud
- Fibonacci Levels, Support/Resistance
- Volume Profile, Divergence Detection

### Missing Technical Features

| Feature | Source | Availability | Priority |
|---------|--------|--------------|----------|
| **Weighted Alpha** | Barchart | 🟡 Calculate (1-year weighted performance) | Medium |
| **RSL (Relative Strength Levy)** | Onvista | 🟡 Calculate (Price / SMA) | Low |
| **Momentum Indicator** | Onvista | 🟡 Calculate (Price change over N days) | Medium |
| **Key Turning Points** | Barchart | 🟡 Calculate pivot points | ⭐ High |
| **Support/Resistance Levels (3 levels)** | Barchart | 🟡 Enhance existing implementation | High |
| **Barchart Technical Opinion Score** | Barchart | 🔴 Proprietary algorithm | Medium |
| **14-Day RSI Interpretation** | Barchart | 🟢 Add interpretation logic | Medium |
| **SMA Distance %** | Finviz | 🟢 Already have data, add display | ⭐ High |
| **Performance by Period** | All sites | 🟢 Calculate from price data | ⭐ High |
| **52W High/Low Distance %** | Finviz | 🟢 Already calculated | Display only |

### Missing Performance Metrics

| Metric | Source | Availability | Priority |
|--------|--------|--------------|----------|
| **Perf Week/Month/Quarter/Half/Year/YTD** | Finviz | 🟢 Calculate from prices | ⭐ High |
| **Relative Performance vs Index** | Onvista, Finviz | 🟡 Need index data | ⭐ High |
| **Relative Volume** | Finviz | 🟢 yfinance (`averageVolume`) | High |
| **Average Volume (10/20/30 day)** | Multiple | 🟢 Calculate from prices | Medium |

---

## 3. Analyst Ratings & Estimates (Major Gap)

### Currently Implemented ✅
- Basic analyst recommendations from yfinance
- Price targets (high/low/mean)
- Recommendation trend

### Missing Analyst Features

| Feature | Source | Availability | Priority |
|---------|--------|--------------|----------|
| **Individual Analyst Ratings** | MarketBeat | 🔴 Requires paid API | ⭐ High |
| **Analyst Name & Firm** | MarketBeat, Finviz | 🔴 Requires paid API | High |
| **Rating History Timeline** | MarketBeat | 🔴 Requires paid API | High |
| **Upgrade/Downgrade Alerts** | MarketBeat | 🔴 Requires paid API | ⭐ High |
| **Price Target Changes Over Time** | MarketBeat | 🔴 Requires paid API | High |
| **Consensus Rating Score (1-5)** | Barchart | 🟡 Can derive from yfinance | Medium |
| **Rating Distribution Pie Chart** | Barchart | 🟢 Can create from yfinance | ⭐ High |
| **Forecasted Upside %** | MarketBeat | 🟢 Calculate from targets | ⭐ High |
| **Number of Analysts** | Finviz | 🟢 yfinance recommendations | Medium |
| **Analyst Accuracy Ratings** | MarketBeat | 🔴 Proprietary data | Low |

### Earnings Estimates (Major Gap)

| Feature | Source | Availability | Priority |
|---------|--------|--------------|----------|
| **EPS Estimate Current Qtr** | Finviz, CNBC | 🟢 yfinance earnings estimates | ⭐ High |
| **EPS Estimate Next Qtr** | Finviz | 🟢 yfinance earnings estimates | ⭐ High |
| **EPS Estimate Current Year** | Finviz | 🟢 yfinance earnings estimates | High |
| **EPS Estimate Next Year** | Finviz | 🟢 yfinance earnings estimates | High |
| **Earnings Surprise %** | Finviz, CNBC | 🟢 yfinance earnings history | ⭐ High |
| **Earnings Beat/Miss History** | CNBC | 🟢 yfinance earnings history | ⭐ High |
| **Revenue Estimates** | Multiple | 🟢 yfinance revenue estimates | High |
| **Earnings Projections Chart** | CNBC | 🟢 Can visualize yfinance data | ⭐ High |

---

## 4. Options Data (New Feature Category)

### Currently Implemented ✅
- None (options data not implemented)

### Options Features to Add

| Feature | Source | Availability | Priority |
|---------|--------|--------------|----------|
| **Implied Volatility (IV)** | Barchart, Finviz | 🟢 yfinance options | ⭐ High |
| **Historical Volatility** | Barchart | 🟢 Calculate from prices | ⭐ High |
| **IV Percentile** | Barchart | 🟡 Need historical IV data | High |
| **IV Rank** | Barchart | 🟡 Need historical IV data | High |
| **Put/Call Volume Ratio** | Barchart, Finviz | 🟢 yfinance options | ⭐ High |
| **Put/Call Open Interest Ratio** | Barchart | 🟢 yfinance options | High |
| **Options Chain Display** | All sites | 🟢 yfinance options | ⭐ High |
| **Greeks (Delta, Gamma, Theta, Vega)** | MarketBeat | 🟡 Calculate or fetch | Medium |
| **Expected Move** | Barchart | 🟡 Calculate from IV | High |
| **Options Volume** | Barchart | 🟢 yfinance options | Medium |
| **Open Interest** | Barchart | 🟢 yfinance options | Medium |
| **Max Pain** | Various | 🟡 Calculate from OI | Medium |

---

## 5. Institutional Ownership (Major Gap)

### Currently Implemented ✅
- Basic institutional holder data from yfinance (cached)

### Missing Institutional Features

| Feature | Source | Availability | Priority |
|---------|--------|--------------|----------|
| **Institutional Ownership %** | MarketBeat, Finviz | 🟢 yfinance (`institutionalHolders`) | ⭐ High |
| **Number of Institutions** | MarketBeat | 🟢 Count from yfinance | High |
| **Top 10 Holders List** | MarketBeat, Finviz | 🟢 yfinance (`institutionalHolders`) | ⭐ High |
| **Institutional Buying/Selling** | MarketBeat | 🔴 Requires 13F API | ⭐ High |
| **13F Filing History** | MarketBeat | 🔴 Requires SEC EDGAR API | High |
| **Quarterly Ownership Changes** | MarketBeat | 🔴 Requires 13F tracking | High |
| **New Positions / Closed Positions** | MarketBeat | 🔴 Requires 13F tracking | Medium |
| **Institutional Inflows/Outflows** | MarketBeat | 🔴 Requires 13F tracking | Medium |

### Insider Trading (Major Gap)

| Feature | Source | Availability | Priority |
|---------|--------|--------------|----------|
| **Insider Ownership %** | Finviz | 🟢 yfinance (`insiderHolders`) | ⭐ High |
| **Insider Transactions** | Finviz, MarketBeat | 🟢 yfinance (`insiderTransactions`) | ⭐ High |
| **Recent Insider Buys/Sells** | Finviz | 🟢 yfinance insider data | ⭐ High |
| **Insider Transaction History** | MarketBeat | 🟢 yfinance insider data | High |
| **Insider Names & Titles** | Finviz | 🟢 yfinance insider data | Medium |

---

## 6. Short Interest Data

### Currently Implemented ✅
- Basic short interest display

### Missing Short Interest Features

| Feature | Source | Availability | Priority |
|---------|--------|--------------|----------|
| **Short Float %** | Finviz | 🟢 yfinance (`shortPercentOfFloat`) | ⭐ High |
| **Short Ratio (Days to Cover)** | Finviz | 🟢 yfinance (`shortRatio`) | ⭐ High |
| **Short Interest (Shares)** | MarketBeat | 🟢 yfinance (`sharesShort`) | High |
| **Short Interest History** | MarketBeat | 🔴 Requires historical data | High |
| **Short Interest Changes** | MarketBeat | 🔴 Need to track over time | Medium |
| **Short Squeeze Potential** | Various | 🟡 Calculate from metrics | Medium |

---

## 7. ESG / Sustainability Data (Unique to Onvista)

### Currently Implemented ✅
- None

### ESG Features to Add

| Feature | Source | Availability | Priority |
|---------|--------|--------------|----------|
| **Overall ESG Score** | Onvista | 🟢 yfinance (`esgScores`) | ⭐ High |
| **Environmental Score** | Onvista | 🟢 yfinance ESG data | High |
| **Social Score** | Onvista | 🟢 yfinance ESG data | High |
| **Governance Score** | Onvista | 🟢 yfinance ESG data | High |
| **Climate Score** | Onvista | 🟡 May need calculation | Medium |
| **Gender Diversity Score** | Onvista | 🔴 Specialized data source | Low |
| **% Renewable Energy** | Onvista | 🔴 Specialized data source | Low |
| **Carbon Emissions** | Onvista | 🔴 Specialized data source | Low |
| **Women in Management %** | Onvista | 🔴 Specialized data source | Low |
| **Women on Board %** | Onvista | 🔴 Specialized data source | Low |

---

## 8. News & Sentiment Analysis

### Currently Implemented ✅
- None (planned in FUTURE_FEATURES.md)

### News Features to Add

| Feature | Source | Availability | Priority |
|---------|--------|--------------|----------|
| **Recent News Headlines** | All sites | 🟢 yfinance news | ⭐ High |
| **News Sentiment Score** | MarketBeat | 🔴 Requires NLP/API | High |
| **News Source Links** | All sites | 🟢 yfinance news URLs | High |
| **News Timestamp** | All sites | 🟢 yfinance news | Medium |
| **Related News** | Multiple | 🟢 yfinance news | Medium |
| **Social Media Mentions** | MarketBeat | 🔴 Requires social API | Medium |
| **Trending Stocks** | Multiple | 🔴 Requires aggregation | Low |

---

## 9. TheScreener Ratings (Unique to Onvista)

### Currently Implemented ✅
- None

### TheScreener Features

| Feature | Source | Availability | Priority |
|---------|--------|--------------|----------|
| **Revised Earnings Forecast** | Onvista | 🔴 Proprietary (theScreener) | Medium |
| **Valuation Assessment** | Onvista | 🟡 Can build similar logic | Medium |
| **Medium-term Market Trend** | Onvista | 🟡 Can calculate (40-day trend) | Medium |
| **Relative 4-Week Performance** | Onvista | 🟢 Calculate vs S&P 500 | High |
| **Expected KGV (Forward P/E)** | Onvista | 🟢 yfinance forward P/E | High |
| **G/PE Ratio** | Onvista | 🟡 Growth + Dividend / P/E | Medium |
| **Bear Market Factor** | Onvista | 🟡 Calculate beta-based metric | Medium |
| **Bad News Factor** | Onvista | 🔴 Proprietary calculation | Low |
| **Correlation to Index** | Onvista | 🟡 Calculate correlation | Medium |

---

## 10. UI/UX & Visualization Enhancements

### Currently Implemented ✅
- Candlestick/Line charts, RSI/MACD sub-charts
- Volume bars, Sparklines
- Seasonality heatmap, Sector comparison
- Correlation heatmap, Market breadth dashboard

### Missing UI Features

| Feature | Source | Availability | Priority |
|---------|--------|--------------|----------|
| **Comparison Chart (vs Index/Peers)** | Onvista, All | 🟢 Have data | ⭐ High |
| **Benchmark Overlay on Chart** | Onvista | 🟢 Have data | ⭐ High |
| **Key Stats Card Layout** | All sites | N/A (UI only) | ⭐ High |
| **Analyst Rating Pie Chart** | Barchart | 🟢 Have data | ⭐ High |
| **Earnings History Bar Chart** | CNBC | 🟢 Have data | ⭐ High |
| **Price Target Range Visualization** | MarketBeat | 🟢 Have data | High |
| **Institutional Buying/Selling Chart** | MarketBeat | 🔴 Need data | High |
| **Options Chain Table** | Barchart, MarketBeat | 🟢 yfinance | High |
| **Put/Call Ratio Chart** | Barchart | 🟢 yfinance | Medium |
| **Short Interest History Chart** | MarketBeat | 🔴 Need historical | Medium |
| **Peer Comparison Table** | Onvista, Finviz | 🟢 Have data | ⭐ High |
| **Company Logo Display** | All sites | 🔴 Need logo source | Medium |
| **Dark Mode Toggle** | Barchart | N/A (UI only) | Low |

---

## 11. Calendar & Events

### Currently Implemented ✅
- Basic earnings date display

### Missing Calendar Features

| Feature | Source | Availability | Priority |
|---------|--------|--------------|----------|
| **Earnings Calendar View** | Onvista, All | 🟢 yfinance earnings dates | ⭐ High |
| **Dividend Calendar** | MarketBeat | 🟢 yfinance dividend dates | High |
| **Ex-Dividend Date** | Finviz | 🟢 yfinance (`exDividendDate`) | High |
| **Stock Split History** | MarketBeat | 🟢 yfinance actions | Medium |
| **IPO Date** | Finviz | 🔴 Need data source | Low |
| **Corporate Events Calendar** | Multiple | 🔴 Need data source | Low |

---

## 12. Company Profile Enhancements

### Currently Implemented ✅
- Basic company info (name, sector, industry, description)

### Missing Profile Features

| Feature | Source | Availability | Priority |
|---------|--------|--------------|----------|
| **Full Business Description** | All sites | 🟢 yfinance (`longBusinessSummary`) | High |
| **Company Officers/Executives** | Finviz | 🟢 yfinance (`companyOfficers`) | Medium |
| **Employee Count** | Finviz | 🟢 yfinance (`fullTimeEmployees`) | Medium |
| **Headquarters Location** | All sites | 🟢 yfinance company info | Medium |
| **Website URL** | All sites | 🟢 yfinance (`website`) | Low |
| **Phone Number** | MarketBeat | 🟢 yfinance (`phone`) | Low |
| **Year Founded** | MarketBeat | 🔴 Need data source | Low |
| **SIC/NAICS Codes** | Barchart | 🔴 Need data source | Low |
| **Index Membership** | Finviz | 🟡 Need index constituent data | Medium |

---

## 13. Screener Enhancements

### Currently Implemented ✅
- Basic filters (P/E, Market Cap, RSI, Volume, etc.)

### Missing Screener Filters

| Filter | Source | Availability | Priority |
|--------|--------|--------------|----------|
| **Forward P/E Range** | Finviz | 🟢 yfinance | ⭐ High |
| **PEG Ratio Range** | Finviz | 🟢 yfinance | ⭐ High |
| **EV/EBITDA Range** | Finviz | 🟢 yfinance | High |
| **Quick/Current Ratio** | Finviz | 🟢 yfinance | Medium |
| **Insider Ownership %** | Finviz | 🟢 yfinance | High |
| **Institutional Ownership %** | Finviz | 🟢 yfinance | High |
| **Short Float %** | Finviz | 🟢 yfinance | ⭐ High |
| **Performance Filters (1W, 1M, etc.)** | Finviz | 🟢 Calculate | ⭐ High |
| **Analyst Recommendation** | Finviz | 🟢 yfinance | High |
| **Earnings Date Filter** | Finviz | 🟢 yfinance | High |
| **Optionable Filter** | Finviz | 🟢 yfinance | Medium |
| **Country Filter** | Finviz | 🟢 yfinance | Medium |
| **IPO Date Filter** | Finviz | 🔴 Need data | Low |

---

## Implementation Recommendations

### Phase 1: Quick Wins (1-2 weeks)
*Features using existing yfinance data with minimal effort*

1. ⭐ **Forward P/E, PEG, EV/EBITDA** - Add to fundamentals display
2. ⭐ **Performance by Period** - 1D, 1W, 1M, 3M, 6M, YTD, 1Y calculations
3. ⭐ **Earnings Estimates & Surprise** - Visualize existing yfinance data
4. ⭐ **Analyst Rating Pie Chart** - Create visualization
5. ⭐ **Insider Transactions Display** - Show yfinance insider data
6. ⭐ **Short Interest Metrics** - Display existing data better
7. ⭐ **Institutional Top Holders** - Display yfinance holder data

### Phase 2: Medium Effort (2-4 weeks)
*Features requiring calculations or new components*

1. ⭐ **Options Overview** - IV, Put/Call ratios, basic chain
2. ⭐ **ESG Scores Display** - yfinance ESG data
3. **Benchmark Comparison** - Chart overlay with index
4. **Earnings History Chart** - Beat/miss visualization
5. **Price Target Visualization** - Range display
6. **Key Turning Points** - Pivot point calculations
7. **Growth Metrics** - YoY/QoQ calculations

### Phase 3: Major Features (4-8 weeks)
*Features requiring significant development or new data sources*

1. ⭐ **Full Options Chain** - Interactive options display
2. **News Integration** - yfinance news with display
3. **13F Institutional Tracking** - Requires SEC EDGAR API
4. **Individual Analyst Ratings** - Requires paid API (Benzinga, etc.)
5. **Historical IV Tracking** - Need to collect over time
6. **Comprehensive Calendar** - Earnings, dividends, splits

### Phase 4: Future Enhancements
*Nice-to-have features, lower priority*

1. ESG detailed breakdown (specialized data)
2. TheScreener-style ratings (proprietary)
3. Social sentiment analysis
4. Company logo integration
5. Advanced peer comparison tools

---

## Data Source Summary

| Data Source | What It Provides | Cost |
|-------------|------------------|------|
| **yfinance** | 80% of needed data | Free |
| **SEC EDGAR** | 13F filings, insider transactions | Free |
| **Benzinga** | Analyst ratings, news | Paid |
| **Alpha Vantage** | Fundamentals, technicals | Free tier available |
| **Polygon.io** | Real-time data, options | Paid |
| **IEX Cloud** | Wide range of data | Paid |
| **Refinitiv/LSEG** | Comprehensive (enterprise) | Expensive |

---

## Conclusion

Our Stock-Watchlist application has a solid foundation with comprehensive technical analysis and charting capabilities. The main gaps compared to commercial platforms are:

1. **Analyst Data Depth** - Individual analyst ratings and history
2. **Options Data** - Completely missing feature category
3. **Institutional Tracking** - 13F filing history and trends
4. **Earnings Visualization** - Beat/miss history, estimates charts
5. **Performance Metrics** - Period-based performance display
6. **ESG Data** - Growing importance, yfinance provides basics

**Recommended Priority:** Focus on Phase 1 & 2 items first, as they provide maximum value with existing data sources and reasonable development effort.