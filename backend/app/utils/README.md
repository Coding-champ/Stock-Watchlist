# Backend Utils

Zentrale Utility-Funktionen für die Stock-Watchlist Anwendung.

## 📦 Module

### 🎯 signal_interpretation.py
Signal-Interpretation für technische Indikatoren.

**Funktionen:**
- `interpret_rsi(rsi: float) -> str` - Interpretiert RSI Werte (0-100)
  - Returns: `'overbought'`, `'oversold'`, `'bullish'`, `'bearish'`, `'neutral'`
  
- `interpret_macd(histogram: float) -> str` - Interpretiert MACD Histogramm
  - Returns: `'bullish'`, `'bearish'`, `'neutral'`

**Beispiel:**
```python
from backend.app.utils.signal_interpretation import interpret_rsi, interpret_macd

rsi_signal = interpret_rsi(75.0)  # 'overbought'
macd_signal = interpret_macd(1.5)  # 'bullish'
```

---

### 🧹 json_serialization.py
JSON Serialisierung und Data Cleaning.

**Funktionen:**
- `clean_for_json(data: Any) -> Any` - Konvertiert numpy/pandas Types zu Python Types
- `clean_json_floats(obj: Any) -> Any` - Ersetzt NaN/Infinity mit None

**Beispiel:**
```python
from backend.app.utils.json_serialization import clean_for_json, clean_json_floats
import numpy as np

# Numpy zu Python konvertieren
data = {'price': np.float64(123.45), 'volume': np.int64(1000)}
clean_data = clean_for_json(data)
# {'price': 123.45, 'volume': 1000}

# NaN/Infinity behandeln
float_data = {'value': float('nan'), 'other': float('inf')}
clean_floats = clean_json_floats(float_data)
# {'value': None, 'other': None}
```

---

### 📅 time_series_utils.py
Zeitreihen und Datum-Verarbeitung.

**Funktionen:**
- `calculate_period_cutoff_date(end_date: pd.Timestamp, period: str) -> Optional[pd.Timestamp]`
  - Berechnet Start-Datum für einen Period-String (z.B. '1y', '3mo')
  
- `filter_indicators_by_dates(indicators_result: Dict, target_dates: List[str]) -> Dict`
  - Filtert Indikator-Daten auf bestimmte Datumsbereiche
  
- `format_period_string(period_date) -> str`
  - Formatiert Datum zu "FY2025Q3" Format
  
- `estimate_required_warmup_bars(indicators: Optional[List[str]]) -> Optional[int]`
  - Schätzt benötigte Warmup-Bars für Indikator-Berechnung

**Beispiel:**
```python
from backend.app.utils.time_series_utils import (
    calculate_period_cutoff_date,
    format_period_string,
    estimate_required_warmup_bars
)
import pandas as pd
from datetime import datetime

# Period Cutoff berechnen
end = pd.Timestamp(datetime.now())
cutoff = calculate_period_cutoff_date(end, '1y')
print(f"Start: {cutoff}, End: {end}")

# Period String formatieren
period = pd.Timestamp('2025-09-30')
formatted = format_period_string(period)  # 'FY2025Q3'

# Warmup Bars schätzen
indicators = ['sma_50', 'sma_200', 'rsi']
warmup = estimate_required_warmup_bars(indicators)  # 240 (200 * 1.2)
```

---

## 🔄 Migration von Legacy Code

Alle bestehenden Funktionen in Services sind **DEPRECATED** aber funktionieren weiterhin:

```python
# ❌ Alt (funktioniert, aber deprecated)
from backend.app.services.technical_indicators_service import _interpret_rsi
signal = _interpret_rsi(70.0)

# ✅ Neu (empfohlen)
from backend.app.utils.signal_interpretation import interpret_rsi
signal = interpret_rsi(70.0)
```

---

## 🧪 Testing

Alle Utils sind unit-testbar:

```bash
# Alle Utils testen
pytest backend/tests/test_utils/

# Einzelne Module
pytest backend/tests/test_utils/test_signal_interpretation.py
pytest backend/tests/test_utils/test_json_serialization.py
pytest backend/tests/test_utils/test_time_series_utils.py
```

---

## 📚 Import Best Practices

### Einzelne Funktionen importieren (empfohlen)
```python
from backend.app.utils.signal_interpretation import interpret_rsi
from backend.app.utils.json_serialization import clean_for_json
```

### Alle Utils aus Hauptmodul
```python
from backend.app.utils import (
    interpret_rsi,
    interpret_macd,
    clean_for_json,
    clean_json_floats
)
```

### Modul importieren
```python
from backend.app.utils import signal_interpretation
signal = signal_interpretation.interpret_rsi(75.0)
```

---

## 🎯 Wartbarkeit

**Single Source of Truth:** Alle Helper-Funktionen sind zentral definiert.

**Vorteile:**
- ✅ Keine Code-Duplikation
- ✅ Einfachere Tests
- ✅ Konsistentes Verhalten
- ✅ Einfache Wartung

**Bei Änderungen:**
1. Funktion in `backend/app/utils/*.py` anpassen
2. Tests aktualisieren
3. Fertig! Alle Services nutzen automatisch die neue Version

---

## 📝 Contributing

Neue Utils hinzufügen:

1. Neue Funktion in passendem Modul erstellen (oder neues Modul anlegen)
2. Funktion in `__init__.py` exportieren
3. Unit Tests schreiben
4. Dokumentation hier aktualisieren

**Beispiel:**
```python
# In backend/app/utils/signal_interpretation.py
def interpret_bollinger(position: str, squeeze: bool) -> str:
    """Interpretiert Bollinger Band Position"""
    if squeeze:
        return 'squeeze'
    return 'overbought' if position == 'above_upper' else 'oversold'

# In backend/app/utils/__init__.py
from .signal_interpretation import interpret_rsi, interpret_macd, interpret_bollinger

__all__ = [..., 'interpret_bollinger']
```

---

**Erstellt:** 2025-11-04  
**Autor:** GitHub Copilot  
**Version:** 1.0.0
