# 📊 Berechnete Metriken - Dokumentation

## Übersicht

Das Stock-Watchlist-System bietet nun umfassende **berechnete Metriken** zur detaillierten Aktienanalyse. Diese Metriken werden in Echtzeit aus den verfügbaren Marktdaten berechnet und bieten tiefe Einblicke in:

- Technische Indikatoren
- Bewertungskennzahlen
- Qualitäts-Scores
- Risiko-Metriken
- Dividenden-Sicherheit
- Analystendaten

---

## 📋 Drei Phasen der Analyse

### **Phase 1: Basis-Indikatoren**

Grundlegende technische und fundamentale Metriken für einen schnellen Überblick.

#### 52-Wochen-Metriken
- **distance_from_52w_high**: Abstand vom 52-Wochen-Hoch (%)
- **distance_from_52w_low**: Abstand vom 52-Wochen-Tief (%)
- **position_in_52w_range**: Position in der 52-Wochen-Spanne (0-100%)

#### Gleitende Durchschnitte (SMA)
- **distance_from_sma50**: Abstand vom 50-Tage-Durchschnitt (%)
- **distance_from_sma200**: Abstand vom 200-Tage-Durchschnitt (%)
- **golden_cross**: Bullisches Signal (SMA50 > SMA200)
- **death_cross**: Bärisches Signal (SMA50 < SMA200)
- **trend**: Aktueller Trend ('bullish', 'bearish', 'neutral')

#### Volumen-Analyse
- **relative_volume**: Aktuelles Volumen relativ zum Durchschnitt
- **volume_category**: Kategorisierung ('very_low', 'low', 'normal', 'high', 'very_high')

#### Cashflow
- **fcf_yield**: Free Cashflow Yield (%)

---

### **Phase 2: Bewertungs-Scores**

Quantitative Bewertung der Aktienqualität und -bewertung.

#### Value Score (0-100)
Kombinierte Bewertungsmetrik aus:
- **PE Score**: Basierend auf Kurs-Gewinn-Verhältnis
- **PB Score**: Basierend auf Kurs-Buchwert-Verhältnis
- **PS Score**: Basierend auf Kurs-Umsatz-Verhältnis
- **Kategorien**: 'undervalued' (≥70), 'fair' (40-69), 'overvalued' (<40)

#### Quality Score (0-100)
Fundamentale Unternehmensqualität:
- **ROE Score**: Return on Equity Bewertung
- **ROA Score**: Return on Assets Bewertung
- **Profitability Score**: Gewinn- und operative Margen
- **Financial Health Score**: Verschuldungsgrad
- **Kategorien**: 'excellent' (≥80), 'good' (60-79), 'average' (40-59), 'poor' (<40)

#### Dividend Safety Score (0-100)
Dividendensicherheit und -nachhaltigkeit:
- **Payout Sustainability**: Ausschüttungsquoten-Analyse
- **Yield Sustainability**: Vergleich mit historischem Durchschnitt
- **Dividend Growth Potential**: Free Cashflow-Deckung
- **Kategorien**: 'very_safe', 'safe', 'moderate', 'risky', 'very_risky'

#### PEG Ratio
Preis/Gewinn-Wachstums-Verhältnis (wenn nicht direkt verfügbar)

---

### **Phase 3: Erweiterte Analyse**

Fortgeschrittene technische Indikatoren und Risikometriken.

#### MACD (Moving Average Convergence Divergence)
- **macd_line**: MACD-Linie
- **signal_line**: Signal-Linie
- **histogram**: MACD-Histogramm
- **trend**: Trend-Signal ('bullish', 'bearish', 'neutral')

#### Stochastic Oscillator
- **k_percent**: %K-Wert (0-100)
- **d_percent**: %D-Wert (0-100)
- **signal**: Marktsignal ('overbought', 'oversold', 'neutral')
- **is_overbought**: Überkauft-Status (K ≥ 80)
- **is_oversold**: Überverkauft-Status (K ≤ 20)

#### Volatilitäts-Metriken
Annualisierte Volatilität für verschiedene Zeiträume:
- **volatility_30d**: 30-Tage-Volatilität (%)
- **volatility_90d**: 90-Tage-Volatilität (%)
- **volatility_1y**: 1-Jahres-Volatilität (%)
- **Kategorien**: 'very_low' (<15%), 'low' (15-25%), 'moderate' (25-40%), 'high' (40-60%), 'very_high' (>60%)

#### Maximum Drawdown
- **max_drawdown**: Größter Kursrückgang vom Hoch (%)
- **current_drawdown**: Aktueller Drawdown (%)
- **max_drawdown_duration**: Dauer des maximalen Drawdowns (Tage)

#### Analystendaten
- **upside_potential**: Kurspotenzial bis zum Analystenziel (%)
- **target_mean**: Durchschnittliches Kursziel
- **target_high**: Höchstes Kursziel
- **target_low**: Niedrigstes Kursziel
- **consensus_strength**: Einigkeit der Analysten ('strong', 'moderate', 'weak')
- **recommendation_score**: Durchschnittliche Empfehlung (1=Strong Buy, 5=Strong Sell)
- **number_of_analysts**: Anzahl der Analysten

#### Beta-Adjustierte Metriken (Risiko-bereinigte Performance)
**Sharpe Ratio:**
- Überrendite pro Einheit Gesamtrisiko
- Interpretation: >1.5=Sehr gut, >1.0=Gut, >0.5=Akzeptabel, <0.5=Schlecht

**Alpha:**
- Überrendite gegenüber CAPM-Erwartung (%)
- Interpretation: >3%=Sehr gut, >1%=Gut, >0%=Positiv, <0%=Underperformance

**Treynor Ratio:**
- Überrendite pro Einheit Beta-Risiko
- Interpretation: >0.15=Exzellent, >0.10=Gut, >0.05=Akzeptabel

**Sortino Ratio:**
- Wie Sharpe, aber nur Downside-Risiko
- Interpretation: >2.0=Sehr gut, >1.5=Gut, >1.0=Akzeptabel

**Beta-Adjusted Return:**
- Rendite normalisiert auf Beta=1.0 (%)
- Zeigt "echte" Rendite ohne Beta-Effekt

**Information Ratio:**
- Konsistenz der Outperformance
- Interpretation: >1.0=Exzellent, >0.75=Sehr gut, >0.5=Gut

**Weitere Metriken:**
- **downside_deviation**: Negative Volatilität (%)
- **total_return**: Gesamtrendite über Periode (%)
- **annualized_return**: Auf Jahr hochgerechnet (%)
- **risk_rating**: Gesamt-Risiko ('low', 'moderate', 'high', 'very_high')

#### Risk-Adjusted Performance Score (0-100)
Kombinierter Score aus allen Beta-Metriken:
- **overall_score**: Gewichteter Durchschnitt (0-100)
- **rating**: 'excellent' (≥80), 'good' (≥65), 'average' (≥45), 'poor' (<45)
- **Einzelbeiträge**: Sharpe (30%), Alpha (30%), Sortino (25%), Information (15%)

---

## 🔌 API-Endpunkte

### 1. Berechnete Metriken abrufen

```http
GET /api/stock-data/{stock_id}/calculated-metrics
```

**Query-Parameter:**
- `period` (optional): Zeitraum für historische Daten ('1mo', '3mo', '6mo', '1y', '2y')
  - Standard: '1y'
- `use_cache` (optional): Cache verwenden
  - Standard: true

**Response:**
```json
{
  "phase1_basic_indicators": {
    "week_52_metrics": { ... },
    "sma_metrics": { ... },
    "volume_metrics": { ... },
    "fcf_yield": 2.48
  },
  "phase2_valuation_scores": {
    "peg_ratio": 2.5,
    "value_metrics": { ... },
    "quality_metrics": { ... },
    "dividend_metrics": { ... }
  },
  "phase3_advanced_analysis": {
    "macd": { ... },
    "stochastic": { ... },
    "volatility": { ... },
    "drawdown": { ... },
    "analyst_metrics": { ... }
  },
  "calculation_timestamp": "2025-10-04T..."
}
```

### 2. Stock mit berechneten Metriken

```http
GET /api/stocks/{stock_id}/with-calculated-metrics
```

**Query-Parameter:**
- `period` (optional): Zeitraum für technische Indikatoren
- `force_refresh` (optional): Cache-Aktualisierung erzwingen

**Response:**
Vollständiges Stock-Objekt inkl. Extended Data und Calculated Metrics

---

## 💡 Verwendungsbeispiele

### Beispiel 1: Überverkaufte Aktien finden

Verwende den Stochastic Oscillator:

```python
# Aktie ist überverkauft, wenn:
stochastic['is_oversold'] == True  # K <= 20
stochastic['signal'] == 'oversold'
```

### Beispiel 2: Qualitätsaktien identifizieren

Kombiniere Quality und Value Scores:

```python
# Hochwertige Aktie mit fairer Bewertung:
quality_metrics['quality_score'] >= 70  # Good/Excellent
value_metrics['value_score'] >= 40      # Fair/Undervalued
```

### Beispiel 3: Dividenden-Aristokraten finden

Nutze Dividend Safety Score:

```python
# Sichere Dividendenaktie:
dividend_metrics['dividend_safety_score'] >= 80
dividend_metrics['safety_category'] in ['very_safe', 'safe']
dividend_info['dividend_yield'] >= 0.03  # >= 3%
```

### Beispiel 4: Trend-Bestätigung

Mehrere Indikatoren kombinieren:

```python
# Starker Bullischer Trend:
sma_metrics['golden_cross'] == True
sma_metrics['trend'] == 'bullish'
macd['trend'] == 'bullish'
macd['histogram'] > 0
```

### Beispiel 5: Risiko-Assessment

Volatilität und Drawdown analysieren:

```python
# Niedriges Risiko:
volatility['volatility_30d'] < 20
volatility['volatility_category'] in ['very_low', 'low']
abs(drawdown['current_drawdown']) < 5
```

---

## 🎯 Best Practices

### 1. **Caching nutzen**
Die Berechnungen sind ressourcenintensiv. Nutze den Cache:
```python
use_cache=True  # Standard-Einstellung
```
Cache-Laufzeit: 1 Stunde

### 2. **Zeiträume anpassen**
Für kurzfristige Analyse:
```python
period="3mo"  # 3 Monate für aktuelle Trends
```

Für langfristige Analyse:
```python
period="2y"   # 2 Jahre für stabilere Indikatoren
```

### 3. **Null-Werte behandeln**
Nicht alle Metriken sind immer verfügbar:
```python
if metrics['phase2_valuation_scores']['peg_ratio']:
    # PEG Ratio verfügbar
    pass
```

### 4. **Kategorien nutzen**
Verwende Kategorien für einfache Entscheidungen:
```python
if value_metrics['value_category'] == 'undervalued':
    # Potentiell unterbewertet
    pass
```

---

## 🔍 Performance-Hinweise

### Berechnungszeit
- **Phase 1:** ~0.1s (keine historischen Daten)
- **Phase 2:** ~0.1s (keine historischen Daten)
- **Phase 3:** ~1-2s (benötigt historische Daten)
- **Gesamt:** ~1-2s (mit Cache deutlich schneller)

### Optimierungen
1. **Cache aktivieren**: Reduziert API-Calls zu yfinance
2. **Kürzere Perioden**: Weniger Daten = schnellere Berechnung
3. **Selektive Abfrage**: Nur benötigte Metriken berechnen

---

## 🐛 Troubleshooting

### Problem: Metriken sind NULL
**Ursache:** Daten nicht verfügbar von yfinance
**Lösung:** 
- Prüfe ob Ticker-Symbol korrekt ist
- Manche Metriken nur für große Unternehmen verfügbar
- Bei kleineren Aktien oft unvollständige Daten

### Problem: Langsame Berechnung
**Ursache:** Erste Berechnung oder Cache abgelaufen
**Lösung:**
- Warte auf Caching (1h Laufzeit)
- Nutze kürzere Perioden für schnellere Antwort
- Background-Tasks für vorherige Berechnung

### Problem: Historische Daten fehlen
**Ursache:** Aktie zu neu oder wenig Handelsvolumen
**Lösung:**
- Phase 3 Metriken nur verfügbar bei ausreichend Historie
- Mindestens 30 Tage für Basis-Indikatoren
- 252 Tage (1 Jahr) für vollständige Analyse

---

## 📚 Weiterführende Ressourcen

### Technische Indikatoren
- **RSI**: Relative Strength Index (bereits in StockData)
- **MACD**: [Investopedia MACD](https://www.investopedia.com/terms/m/macd.asp)
- **Stochastic**: [Investopedia Stochastic](https://www.investopedia.com/terms/s/stochasticoscillator.asp)

### Bewertungskennzahlen
- **PEG Ratio**: [Investopedia PEG](https://www.investopedia.com/terms/p/pegratio.asp)
- **ROE/ROA**: [Investopedia ROE](https://www.investopedia.com/terms/r/returnonequity.asp)

### Risikometriken
- **Maximum Drawdown**: [Investopedia Drawdown](https://www.investopedia.com/terms/m/maximum-drawdown-mdd.asp)
- **Volatilität**: [Investopedia Volatility](https://www.investopedia.com/terms/v/volatility.asp)

---

## 🔄 Zukünftige Erweiterungen

Geplante Features:
- [ ] Sektor- und Peer-Vergleich
- [ ] Zusätzliche technische Indikatoren (Williams %R, MFI)
- [ ] Backtest-Funktionalität
- [ ] ML-basierte Prognosen
- [ ] Benutzerdefinierte Scoring-Gewichtungen
- [ ] Alert-System basierend auf berechneten Metriken

---

*Dokumentation Version 1.0 - Stand: 04.10.2025*
