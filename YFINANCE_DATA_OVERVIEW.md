# yfinance Datenmöglichkeiten - Komplette Übersicht

Diese Dokumentation zeigt alle verfügbaren Datentypen und -kategorien der yfinance-Bibliothek für die Aktienanalyse.

## 📊 **FUNDAMENTALDATEN**

### Unternehmensinformationen
| Datenfeld | Beschreibung | Typ |
|-----------|--------------|-----|
| `longName` / `shortName` | Vollständiger/Kurzer Firmenname | string |
| `sector` | Wirtschaftssektor | string |
| `industry` | Branche/Industrie | string |
| `longBusinessSummary` | Geschäftsbeschreibung | string |
| `fullTimeEmployees` | Anzahl Vollzeitbeschäftigte | int |
| `website` | Unternehmens-Website | string |
| `phone` | Telefonnummer | string |
| `address1`, `city`, `state`, `zip`, `country` | Adressdaten | string |
| `companyOfficers` | Führungskräfte und Vorstand | list |

### Finanzielle Kennzahlen
| Datenfeld | Beschreibung | Typ |
|-----------|--------------|-----|
| `marketCap` | Marktkapitalisierung | float |
| `enterpriseValue` | Unternehmenswert | float |
| `trailingPE` | KGV (historisch) | float |
| `forwardPE` | KGV (prognostiziert) | float |
| `pegRatio` | PEG-Ratio | float |
| `priceToBook` | Kurs-Buchwert-Verhältnis | float |
| `priceToSalesTrailing12Months` | Kurs-Umsatz-Verhältnis | float |
| `enterpriseToRevenue` | EV/Umsatz | float |
| `enterpriseToEbitda` | EV/EBITDA | float |
| `profitMargins` | Gewinnmarge (Dezimal: 0.24 = 24%) | float |
| `operatingMargins` | Operative Marge (Dezimal: 0.30 = 30%) | float |
| `returnOnAssets` | Gesamtkapitalrendite ROA (Dezimal: 0.25 = 25%) | float |
| `returnOnEquity` | Eigenkapitalrendite ROE (Dezimal: 1.50 = 150%) | float |
| `revenueGrowth` | Umsatzwachstum | float |
| `earningsGrowth` | Gewinnwachstum | float |

### Bilanz & Cashflow
| Datenfeld | Beschreibung | Typ |
|-----------|--------------|-----|
| `totalCash` | Gesamte Liquidität | float |
| `totalCashPerShare` | Liquidität pro Aktie | float |
| `totalDebt` | Gesamtverschuldung | float |
| `debtToEquity` | Verschuldungsgrad | float |
| `currentRatio` | Liquiditätsgrad 1 | float |
| `quickRatio` | Liquiditätsgrad 2 | float |
| `operatingCashflow` | Operativer Cashflow | float |
| `freeCashflow` | Freier Cashflow | float |

### Dividenden
| Datenfeld | Beschreibung | Typ |
|-----------|--------------|-----|
| `dividendRate` | Jährliche Dividende | float |
| `dividendYield` | Dividendenrendite (bereits in %) | float |
| `payoutRatio` | Ausschüttungsquote (Dezimal: 0.15 = 15%) | float |
| `fiveYearAvgDividendYield` | 5-Jahres Ø Dividendenrendite (bereits in %) | float |
| `exDividendDate` | Ex-Dividenden-Datum | timestamp |

## 📈 **TECHNISCHE INDIKATOREN & MARKTDATEN**

### Preisdaten
| Datenfeld | Beschreibung | Typ |
|-----------|--------------|-----|
| `currentPrice` / `regularMarketPrice` | Aktueller Kurs | float |
| `previousClose` | Vorheriger Schlusskurs | float |
| `open` / `regularMarketOpen` | Eröffnungskurs | float |
| `dayLow` / `regularMarketDayLow` | Tagestief | float |
| `dayHigh` / `regularMarketDayHigh` | Tageshoch | float |
| `fiftyTwoWeekLow` | 52-Wochen-Tief | float |
| `fiftyTwoWeekHigh` | 52-Wochen-Hoch | float |
| `fiftyDayAverage` | 50-Tage gleitender Durchschnitt | float |
| `twoHundredDayAverage` | 200-Tage gleitender Durchschnitt | float |

### Handelsvolumen
| Datenfeld | Beschreibung | Typ |
|-----------|--------------|-----|
| `volume` / `regularMarketVolume` | Tagesvolumen | int |
| `averageVolume` | Durchschnittsvolumen | int |
| `averageVolume10days` | 10-Tage Durchschnittsvolumen | int |
| `averageDailyVolume10Day` | Tägliches Durchschnittsvolumen | int |
| `bid` | Geldkurs | float |
| `ask` | Briefkurs | float |
| `bidSize` | Geld-Ordervolumen | int |
| `askSize` | Brief-Ordervolumen | int |

### Volatilität & Risiko
| Datenfeld | Beschreibung | Typ |
|-----------|--------------|-----|
| `beta` | Beta-Faktor (Marktrisiko) | float |
| `impliedSharesOutstanding` | Aktien im Umlauf | int |
| `floatShares` | Free Float | int |
| `sharesOutstanding` | Ausgegebene Aktien | int |
| `heldPercentInsiders` | Insider-Anteil | float |
| `heldPercentInstitutions` | Institutionsanteil | float |

## 📉 **CHART- UND KURSDATEN**

### Historische Kursdaten
```python
# Verfügbare Zeiträume
periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]

# Verfügbare Intervalle
intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]

# Verwendung
ticker.history(period="1y", interval="1d")
```

### Corporate Actions
| Methode | Beschreibung | Rückgabe |
|---------|--------------|----------|
| `ticker.dividends` | Dividendenhistorie | pandas.Series |
| `ticker.splits` | Stock Split Historie | pandas.Series |
| `ticker.actions` | Alle Corporate Actions | pandas.DataFrame |
| `ticker.capital_gains` | Kapitalgewinne (Fonds) | pandas.Series |

### Erweiterte Chartdaten
| Methode | Beschreibung | Rückgabe |
|---------|--------------|----------|
| `ticker.earnings_dates` | Earnings-Termine | pandas.DataFrame |
| `ticker.calendar` | Unternehmenskalender | pandas.DataFrame |
| `ticker.news` | Aktuelle Nachrichten | list |

## 🔍 **ERWEITERTE DATENQUELLEN**

### Analystendaten
| Methode | Beschreibung | Rückgabe |
|---------|--------------|----------|
| `ticker.recommendations` | Analystenbewertungen | pandas.DataFrame |
| `ticker.analyst_price_targets` | Kursziele | pandas.DataFrame |
| `ticker.earnings_estimate` | Gewinnschätzungen | pandas.DataFrame |
| `ticker.revenue_estimate` | Umsatzschätzungen | pandas.DataFrame |
| `ticker.eps_trend` | EPS-Trends | pandas.DataFrame |
| `ticker.eps_revisions` | EPS-Revisionen | pandas.DataFrame |
| `ticker.growth_estimates` | Wachstumsschätzungen | pandas.DataFrame |

### Finanzdokumente
| Methode | Beschreibung | Rückgabe |
|---------|--------------|----------|
| `ticker.financials` | GuV (jährlich) | pandas.DataFrame |
| `ticker.quarterly_financials` | GuV (quartalsweise) | pandas.DataFrame |
| `ticker.balance_sheet` | Bilanz (jährlich) | pandas.DataFrame |
| `ticker.quarterly_balance_sheet` | Bilanz (quartalsweise) | pandas.DataFrame |
| `ticker.cash_flow` | Cashflow (jährlich) | pandas.DataFrame |
| `ticker.quarterly_cash_flow` | Cashflow (quartalsweise) | pandas.DataFrame |
| `ticker.earnings` | Quartalsberichte | pandas.DataFrame |
| `ticker.sec_filings` | SEC-Einreichungen | pandas.DataFrame |

### Optionsdaten
| Methode | Beschreibung | Rückgabe |
|---------|--------------|----------|
| `ticker.options` | Verfügbare Verfallsdaten | tuple |
| `ticker.option_chain(date)` | Optionskette für Datum | OptionChain |

### Insider & Institutionelle Daten
| Methode | Beschreibung | Rückgabe |
|---------|--------------|----------|
| `ticker.insider_transactions` | Insider-Transaktionen | pandas.DataFrame |
| `ticker.insider_purchases` | Insider-Käufe | pandas.DataFrame |
| `ticker.insider_roster_holders` | Insider-Besitzer | pandas.DataFrame |
| `ticker.institutional_holders` | Institutionelle Investoren | pandas.DataFrame |
| `ticker.major_holders` | Großaktionäre | pandas.DataFrame |
| `ticker.mutualfund_holders` | Fondsbesitz | pandas.DataFrame |

### ESG & Governance
| Methode | Beschreibung | Rückgabe |
|---------|--------------|----------|
| `ticker.sustainability` | Nachhaltigkeitsbewertungen | pandas.DataFrame |
| `ticker.upgrades_downgrades` | Rating-Änderungen | pandas.DataFrame |

## 💡 **PRAKTISCHE ANWENDUNGSBEISPIELE**

### 1. Grundlegende Aktieninformationen
```python
import yfinance as yf

ticker = yf.Ticker("AAPL")
info = ticker.info

# Grunddaten
print(f"Unternehmen: {info['longName']}")
print(f"Sektor: {info['sector']}")
print(f"Aktueller Kurs: ${info['currentPrice']:.2f}")
print(f"KGV: {info['trailingPE']:.2f}")
print(f"Marktkapitalisierung: ${info['marketCap']:,}")
```

### 2. Historische Kursdaten
```python
# Verschiedene Zeiträume
hist_1d = ticker.history(period="1d", interval="1m")    # Intraday
hist_1w = ticker.history(period="5d", interval="15m")   # 1 Woche
hist_1m = ticker.history(period="1mo", interval="1h")   # 1 Monat
hist_1y = ticker.history(period="1y", interval="1d")    # 1 Jahr
hist_max = ticker.history(period="max", interval="1wk") # Alle Daten
```

### 3. Technische Indikatoren berechnen
```python
import pandas as pd

# RSI berechnen
def calculate_rsi(prices, window=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

hist = ticker.history(period="1y")
hist['RSI'] = calculate_rsi(hist['Close'])
```

### 4. Dividendeninformationen
```python
# Dividendenhistorie
dividends = ticker.dividends
print(f"Letzte Dividende: ${dividends.iloc[-1]:.2f}")
print(f"Dividendenrendite: {info['dividendYield']:.2%}")

# Alle Dividenden der letzten 5 Jahre
recent_dividends = dividends[dividends.index > '2020-01-01']
```

### 5. Finanzdaten analysieren
```python
# Bilanz
balance_sheet = ticker.balance_sheet
quarterly_balance = ticker.quarterly_balance_sheet

# GuV
income_stmt = ticker.financials
quarterly_income = ticker.quarterly_financials

# Cashflow
cash_flow = ticker.cash_flow
quarterly_cash = ticker.quarterly_cash_flow
```

### 6. News und Events
```python
# Aktuelle News
news = ticker.news
for article in news[:5]:
    print(f"Titel: {article['title']}")
    print(f"Quelle: {article['publisher']}")
    print(f"Link: {article['link']}")
    print("-" * 50)

# Earnings-Termine
earnings_calendar = ticker.calendar
earnings_dates = ticker.earnings_dates
```

### 7. Mehrere Aktien vergleichen
```python
# Mehrere Tickers gleichzeitig
tickers = yf.Tickers("AAPL MSFT GOOGL TSLA")

# Historische Daten für alle
hist_data = tickers.history(period="1y")

# Informationen für alle
for ticker_symbol in ["AAPL", "MSFT", "GOOGL", "TSLA"]:
    ticker_obj = yf.Ticker(ticker_symbol)
    info = ticker_obj.info
    print(f"{ticker_symbol}: {info['longName']} - ${info['currentPrice']:.2f}")
```

## 🚀 **INTEGRATION IN STOCK-WATCHLIST**

### Mögliche Erweiterungen für das aktuelle Projekt:

1. **Erweiterte Fundamentalanalyse**
   - PE-Ratio, PEG-Ratio, Price-to-Book
   - Debt-to-Equity, Current Ratio
   - ROE, ROA, Profit Margins

2. **Technische Analyse Features**
   - RSI, MACD, Bollinger Bänder
   - Gleitende Durchschnitte
   - Volatilitätsberechnung

3. **Portfolio Tracking**
   - Performance-Vergleiche
   - Risikometriken (Beta, Sharpe Ratio)
   - Diversifikationsanalyse

4. **Alert System**
   - Kursziele erreicht
   - Dividenden-Termine
   - Earnings-Veröffentlichungen
   - Technische Signale

5. **News Integration**
   - Aktuelle Nachrichten zu Watchlist-Aktien
   - Sentiment-Analyse
   - Event-basierte Alerts

6. **Vergleichstools**
   - Sektor-/Branchen-Benchmarks
   - Peer-Group-Vergleiche
   - Historische Performance

### Beispiel-Implementierung für erweiterte Stockdaten:
```python
def get_extended_stock_data(ticker_symbol: str):
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    hist = ticker.history(period="1y")
    
    return {
        'basic_info': {
            'name': info.get('longName'),
            'sector': info.get('sector'),
            'current_price': info.get('currentPrice')
        },
        'fundamental_ratios': {
            'pe_ratio': info.get('trailingPE'),
            'peg_ratio': info.get('pegRatio'),
            'price_to_book': info.get('priceToBook'),
            'debt_to_equity': info.get('debtToEquity'),
            'roe': info.get('returnOnEquity')
        },
        'technical_indicators': {
            'beta': info.get('beta'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
            'volume': info.get('volume'),
            'avg_volume': info.get('averageVolume')
        },
        'dividend_info': {
            'dividend_yield': info.get('dividendYield'),
            'payout_ratio': info.get('payoutRatio'),
            'ex_dividend_date': info.get('exDividendDate')
        }
    }
```

---

## ⚠️ **WICHTIGE HINWEISE ZUR DATENINTERPRETATION**

### **Prozentdaten in yfinance:**
yfinance verwendet **unterschiedliche Formate** für Prozentdaten:

**Bereits als Prozent (nicht umrechnen!):**
- `dividendYield: 0.41` = **0.41%**
- `fiveYearAvgDividendYield: 0.54` = **0.54%**

**Als Dezimal (× 100 für Prozent):**
- `payoutRatio: 0.1533` = **15.33%**
- `profitMargins: 0.243` = **24.3%**
- `operatingMargins: 0.300` = **30.0%**
- `returnOnEquity: 1.498` = **149.8%** (kann > 100% sein!)
- `returnOnAssets: 0.245` = **24.5%**

### **Beispiel korrekte Darstellung:**
```javascript
// ❌ FALSCH - Alle × 100
dividendYield: 0.41 × 100 = 41% (viel zu hoch!)

// ✅ RICHTIG - Unterscheidung nach Datentyp
dividendYield: 0.41 → "0.41%"        // bereits Prozent
payoutRatio: 0.1533 × 100 → "15.33%" // Dezimal zu Prozent
```

**Hinweis:** Diese Übersicht zeigt alle verfügbaren yfinance-Datenfelder. Nicht alle Felder sind für jeden Ticker verfügbar. Immer auf `None`-Werte prüfen!