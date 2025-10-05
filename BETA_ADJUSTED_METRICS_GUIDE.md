# 📊 Beta-Adjustierte Metriken - Detaillierte Dokumentation

## Übersicht

Beta-adjustierte Metriken messen die **risikobereinigte Performance** einer Aktie. Sie helfen zu verstehen, ob die erzielten Renditen tatsächlich gut waren im Verhältnis zum eingegangenen Risiko.

---

## 🎯 **Warum sind Beta-adjustierte Metriken wichtig?**

### **Problem ohne Risikoadjustierung:**

```
Aktie A: 25% Rendite, aber sehr volatil (Beta 1.8)
Aktie B: 18% Rendite, aber stabil (Beta 0.9)

Welche ist besser? 🤔
```

**Antwort:** Ohne Risikoadjustierung können wir es nicht sagen! Aktie A könnte nur deshalb mehr Rendite haben, weil sie viel riskanter ist.

### **Mit Beta-adjustierten Metriken:**

Wir können jetzt fragen:
- Wie viel Rendite pro Einheit Risiko?
- Hat die Aktie den Markt geschlagen (Alpha)?
- Ist die hohe Rendite das Risiko wert?

---

## 📈 **Die Beta-Adjustierten Metriken im Detail**

### **1. Sharpe Ratio** ⭐ (Wichtigste Metrik!)

**Formel:**
```
Sharpe Ratio = (Rendite - Risikofreier Zins) / Volatilität
```

**Was misst es?**
Wie viel **Überrendite** (über risikofreie Staatsanleihen) erhalte ich pro Einheit **Gesamtrisiko** (Volatilität)?

**Interpretation:**
- **> 2.0**: Exzellent 🌟🌟🌟
- **> 1.5**: Sehr gut 🌟🌟
- **> 1.0**: Gut 🌟
- **> 0.5**: Akzeptabel ✓
- **< 0.5**: Schlecht ❌

**Beispiel:**
```
Apple (AAPL): Sharpe Ratio = 0.351
Bedeutung: Für jede Einheit Risiko gibt es 0.35 Einheiten Überrendite
→ Rating: Schlecht (unter 0.5)
→ Die Volatilität ist hoch im Verhältnis zur Rendite
```

**Praktische Bedeutung:**
- Investoren bevorzugen höhere Sharpe Ratios
- Vergleichbar zwischen verschiedenen Assets
- Hilft beim Portfolio-Bau

---

### **2. Alpha (α)** 💎

**Formel:**
```
Alpha = Tatsächliche Rendite - Erwartete Rendite (CAPM)
Erwartete Rendite = Risikofreier Zins + Beta × (Marktrendite - Risikofreier Zins)
```

**Was misst es?**
Die **Überrendite** gegenüber dem, was aufgrund des Risikos (Beta) erwartet wurde.

**Interpretation:**
- **> 5%**: Exzellent 🌟🌟🌟
- **> 3%**: Sehr gut 🌟🌟
- **> 1%**: Gut 🌟
- **> 0%**: Positiv ✓
- **< 0%**: Underperformance ❌

**Beispiel:**
```
Apple (AAPL): Alpha = 3.76%
Beta = 1.09
Erwartete Rendite bei Beta 1.09 = 3% + 1.09 × (10% - 3%) = 10.63%
Tatsächliche Rendite = 14.42%
Alpha = 14.42% - 10.63% = 3.76%

Bedeutung: Apple hat 3.76% MEHR Rendite erzielt als erwartet!
→ Das Management/die Aktie hat Mehrwert geschaffen
```

**Praktische Bedeutung:**
- Positives Alpha = Aktie/Manager schlägt den Markt
- Negatives Alpha = Underperformance
- Ziel jedes aktiven Investors: Positives Alpha finden

---

### **3. Treynor Ratio** 📊

**Formel:**
```
Treynor Ratio = (Rendite - Risikofreier Zins) / Beta
```

**Was misst es?**
Wie viel Überrendite pro Einheit **systematisches Risiko** (Beta)?

**Unterschied zu Sharpe:**
- Sharpe: Verwendet Gesamtrisiko (Volatilität)
- Treynor: Verwendet nur Marktrisiko (Beta)

**Interpretation:**
- **> 0.15**: Exzellent
- **> 0.10**: Gut
- **> 0.05**: Akzeptabel
- **< 0.05**: Schlecht

**Beispiel:**
```
Apple (AAPL): Treynor Ratio = 0.104
Bedeutung: Pro Einheit Beta-Risiko gibt es 10.4% Überrendite
→ Rating: Gut
```

**Wann verwenden?**
- Bei diversifizierten Portfolios (unsystematisches Risiko ist weg)
- Zum Vergleich mit anderen Aktien im Portfolio
- Wenn Beta aussagekräftiger ist als Volatilität

---

### **4. Sortino Ratio** 🎯

**Formel:**
```
Sortino Ratio = (Rendite - Risikofreier Zins) / Downside Deviation
```

**Was misst es?**
Wie Sharpe, aber verwendet nur **negative Volatilität** (Downside Risk).

**Warum wichtig?**
- Upside-Volatilität ist gut (große Gewinne)! ✅
- Downside-Volatilität ist schlecht (große Verluste) ❌
- Sortino fokussiert nur auf das "schlechte" Risiko

**Interpretation:**
- **> 2.5**: Exzellent
- **> 2.0**: Sehr gut
- **> 1.5**: Gut
- **> 1.0**: Akzeptabel
- **< 1.0**: Schlecht

**Beispiel:**
```
Apple (AAPL): Sortino Ratio = 0.478
Downside Deviation = 23.89%
Bedeutung: Nur 0.48 Einheiten Überrendite pro Einheit Verlust-Risiko
→ Rating: Schlecht (unter 1.0)
```

**Praktische Bedeutung:**
- Besser als Sharpe für risikoscheue Investoren
- Ignoriert positive Schwankungen
- Fokussiert auf Kapitalerhalt

---

### **5. Beta-Adjusted Return** 🔄

**Formel:**
```
Beta-Adjusted Return = Tatsächliche Rendite / Beta
```

**Was misst es?**
Die Rendite **normalisiert** auf Beta = 1.0.

**Interpretation:**
"Wenn die Aktie nur durchschnittliches Marktrisiko hätte, wäre die Rendite..."

**Beispiel:**
```
Apple (AAPL): 
Tatsächliche Rendite = 14.42%
Beta = 1.09
Beta-Adjusted Return = 14.42% / 1.09 = 13.18%

Bedeutung: 
Bei Beta 1.0 würde Apple 13.18% Rendite erwarten
→ Fairer Vergleich mit Aktien unterschiedlicher Beta-Werte
```

**Wann verwenden?**
- Zum Vergleich aggressiver vs. defensiver Aktien
- Bei Portfolio-Konstruktion mit Ziel-Beta
- Um "echte" Rendite ohne Beta-Effekt zu sehen

---

### **6. Information Ratio** 📈

**Formel:**
```
Information Ratio = (Portfolio Rendite - Benchmark) / Tracking Error
```

**Was misst es?**
Die **Konsistenz** der Outperformance gegenüber dem Markt.

**Interpretation:**
- **> 1.0**: Exzellent (sehr konsistent)
- **> 0.75**: Sehr gut
- **> 0.5**: Gut
- **> 0.25**: Akzeptabel
- **< 0.25**: Inkonsistent

**Beispiel:**
```
Apple (AAPL): Information Ratio = 0.136
Bedeutung: Niedrige Konsistenz bei der Markt-Outperformance
→ Die Überrendite schwankt stark
```

**Praktische Bedeutung:**
- Hohe IR = Verlässliche Outperformance
- Niedrige IR = Glück oder inkonsistent
- Wichtig für aktive Manager-Bewertung

---

### **7. Downside Deviation** 📉

**Formel:**
```
Downside Deviation = Standardabweichung nur der negativen Returns
```

**Was misst es?**
Wie stark sind die **Verluste** im Durchschnitt?

**Interpretation:**
- **< 15%**: Niedrig (wenig Verlustrisiko)
- **15-25%**: Moderat
- **25-40%**: Hoch
- **> 40%**: Sehr hoch

**Beispiel:**
```
Apple (AAPL): Downside Deviation = 23.89%
Bedeutung: In schlechten Zeiten liegt die Volatilität bei ~24%
→ Moderat (im typischen Bereich)
```

---

### **8. Total & Annualized Return** 💰

**Total Return:**
Gesamte Rendite über den Betrachtungszeitraum (z.B. 1 Jahr).

**Annualized Return:**
Auf ein Jahr hochgerechnete Rendite (vergleichbar).

**Beispiel:**
```
Apple (AAPL):
Total Return = 14.29% (über 1 Jahr)
Annualized Return = 14.42%
```

---

## 🎯 **Risk Rating - Automatische Risikoeinstufung**

Basierend auf der Sharpe Ratio wird ein Gesamt-Risiko-Rating vergeben:

```python
if sharpe > 1.5:
    risk_rating = 'low'          # Sehr gutes Risk-Return
elif sharpe > 1.0:
    risk_rating = 'moderate'     # Gutes Risk-Return
elif sharpe > 0.5:
    risk_rating = 'high'         # Akzeptables Risk-Return
else:
    risk_rating = 'very_high'    # Schlechtes Risk-Return
```

**Apple (AAPL) Beispiel:**
```
Sharpe Ratio = 0.351
→ Risk Rating = 'very_high'
→ Die Volatilität ist zu hoch im Verhältnis zur Rendite
```

---

## ⭐ **Risk-Adjusted Performance Score (0-100)**

Ein **kombinierter Score** aus allen Beta-adjustierten Metriken:

### **Berechnung:**

```
Score = 30% Sharpe + 30% Alpha + 25% Sortino + 15% Information Ratio

Jede Komponente wird auf 0-100 skaliert und gewichtet.
```

### **Rating-Kategorien:**

- **≥ 80**: Excellent 🌟🌟🌟 (Top-Performer)
- **≥ 65**: Good 🌟🌟 (Solide Performance)
- **≥ 45**: Average 🌟 (Durchschnittlich)
- **< 45**: Poor ❌ (Unterdurchschnittlich)

### **Apple (AAPL) Beispiel:**

```
Overall Score = 49.8/100
Rating = 'average'

Beiträge:
- Sharpe Contribution: 40.0 (schwach)
- Alpha Contribution: 85.0 (sehr stark!)
- Sortino Contribution: 25.0 (schwach)
- Information Contribution: 40.0 (schwach)

Interpretation:
✅ Starkes Alpha (schlägt Erwartungen)
❌ Schwache Sharpe/Sortino (hohes Risiko)
→ Gute Rendite, aber mit hohem Risiko erkauft
```

---

## 🔍 **Praktische Anwendungsbeispiele**

### **Beispiel 1: Zwei Aktien vergleichen**

```
Tech-Aktie A:
- Rendite: 25%, Beta: 1.8
- Sharpe: 0.8, Alpha: 2%
- Risk Rating: high

Utility-Aktie B:
- Rendite: 15%, Beta: 0.6
- Sharpe: 1.5, Alpha: 4%
- Risk Rating: low

Entscheidung:
→ Aktie B ist besser!
  Warum? Höhere Sharpe, besseres Alpha,
  niedrigeres Risiko trotz niedriger Rendite
```

### **Beispiel 2: Portfolio-Optimierung**

```
Ziel: Sharpe Ratio > 1.0

Aktuelle Aktien:
1. AAPL: Sharpe 0.35 ❌ → Reduzieren
2. MSFT: Sharpe 1.2 ✅ → Halten
3. JNJ: Sharpe 1.8 ✅ → Erhöhen

Strategie: Gewichtung verschieben zu höheren Sharpe Ratios
```

### **Beispiel 3: Risiko-Bewertung**

```
Aktie hat:
- Total Return: 30% ✅
- Sharpe Ratio: 0.4 ❌
- Sortino Ratio: 0.5 ❌
- Risk Rating: very_high ❌

Warnung! Hohe Rendite durch extremes Risiko!
→ Nicht für risikoscheue Investoren geeignet
```

---

## 📊 **Typische Werte nach Asset-Klasse**

### **Sharpe Ratio Benchmarks:**

| Asset-Klasse | Typische Sharpe | Interpretation |
|--------------|-----------------|----------------|
| Large-Cap Stocks | 0.5 - 1.0 | Durchschnittlich |
| Small-Cap Stocks | 0.3 - 0.8 | Volatiler |
| Bonds | 0.8 - 1.5 | Stabiler |
| Hedge Funds | 1.0 - 2.0 | Ziel: Outperformance |
| S&P 500 | 0.5 - 0.8 | Benchmark |

### **Alpha Benchmarks:**

| Performance | Alpha | Häufigkeit |
|-------------|-------|------------|
| Excellent | > 5% | Selten (Top 5%) |
| Good | 2-5% | Gut (Top 20%) |
| Average | 0-2% | Häufig |
| Below | < 0% | Häufig (50%) |

---

## 🎯 **Entscheidungshilfe: Welche Metrik wann?**

### **Für konservative Investoren:**
1. ✅ **Sortino Ratio** (Downside-Fokus)
2. ✅ **Downside Deviation** (Verlust-Risiko)
3. ✅ **Risk Rating** (Gesamt-Risiko)

### **Für Performance-Jäger:**
1. ✅ **Alpha** (Outperformance)
2. ✅ **Information Ratio** (Konsistenz)
3. ✅ **Beta-Adjusted Return** (Echte Rendite)

### **Für Portfolio-Manager:**
1. ✅ **Sharpe Ratio** (Effizienz)
2. ✅ **Treynor Ratio** (Beta-adjustiert)
3. ✅ **Risk-Adjusted Performance Score** (Gesamt)

### **Für Risiko-Management:**
1. ✅ **Risk Rating** (Schnelle Bewertung)
2. ✅ **Sharpe + Sortino** (Risiko-Profile)
3. ✅ **Downside Deviation** (Worst-Case)

---

## 🚨 **Wichtige Einschränkungen**

### **1. Historische Daten**
- Beta und Volatilität sind vergangenheitsbasiert
- Zukünftige Performance kann abweichen
- Marktregime-Änderungen beachten

### **2. Annahmen**
- Risikofreier Zins: 3% (anpassbar)
- Marktrendite: 10% (anpassbar)
- Normal-Verteilung der Returns (oft nicht gegeben)

### **3. Zeitraum-Abhängigkeit**
- 1-Jahres-Daten vs. 5-Jahres-Daten ergeben andere Werte
- Länge des Zeitraums wichtig für Aussagekraft
- Mindestens 1 Jahr empfohlen

### **4. Markt-Timing**
- Start- und Enddatum beeinflussen alle Metriken
- Bull-Market vs. Bear-Market Unterschiede
- Zyklische Effekte beachten

---

## 💡 **Best Practices**

1. **Niemals nur eine Metrik verwenden**
   - Kombiniere mehrere für Gesamt-Bild
   - Risk-Adjusted Performance Score nutzen

2. **Kontext beachten**
   - Sektor-Vergleich (Tech vs. Utilities)
   - Marktphase (Bull vs. Bear)
   - Unternehmensgröße (Large vs. Small Cap)

3. **Regelmäßig aktualisieren**
   - Beta ändert sich über Zeit
   - Quartalsweise Review empfohlen
   - Nach großen Marktevents neu bewerten

4. **Mit Benchmarks vergleichen**
   - Nicht absolut, sondern relativ bewerten
   - S&P 500 als Basis
   - Sektor-spezifische Benchmarks

---

## 📚 **Formeln-Übersicht**

```python
# Sharpe Ratio
sharpe = (return - risk_free_rate) / volatility

# Alpha (CAPM)
alpha = actual_return - (risk_free_rate + beta * (market_return - risk_free_rate))

# Treynor Ratio
treynor = (return - risk_free_rate) / beta

# Sortino Ratio
sortino = (return - risk_free_rate) / downside_deviation

# Beta-Adjusted Return
beta_adjusted = actual_return / beta

# Information Ratio
information_ratio = (return - benchmark_return) / tracking_error
```

---

## 🎓 **Weiterführende Ressourcen**

- [Investopedia: Sharpe Ratio](https://www.investopedia.com/terms/s/sharperatio.asp)
- [Investopedia: Alpha](https://www.investopedia.com/terms/a/alpha.asp)
- [Investopedia: Sortino Ratio](https://www.investopedia.com/terms/s/sortinoratio.asp)
- [Modern Portfolio Theory](https://www.investopedia.com/terms/m/modernportfoliotheory.asp)
- [CAPM Model](https://www.investopedia.com/terms/c/capm.asp)

---

*Dokumentation Version 1.0 - Stand: 04.10.2025*
