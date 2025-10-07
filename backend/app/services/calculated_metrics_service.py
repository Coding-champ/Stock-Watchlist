"""
Service for calculating derived metrics from stock data
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple, List
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ============================================================================
# PHASE 1: BASIS-INDIKATOREN
# ============================================================================

def calculate_52week_distance(current_price: Optional[float], 
                              fifty_two_week_high: Optional[float],
                              fifty_two_week_low: Optional[float]) -> Dict[str, Optional[float]]:
    """
    Berechnet den Abstand vom 52-Wochen-Hoch und -Tief
    
    Returns:
        Dict mit distance_from_52w_high, distance_from_52w_low, position_in_52w_range
    """
    result = {
        'distance_from_52w_high': None,
        'distance_from_52w_low': None,
        'position_in_52w_range': None  # 0-100%, wo 100% = am Hoch
    }
    
    if not current_price:
        return result
    
    if fifty_two_week_high:
        result['distance_from_52w_high'] = ((current_price - fifty_two_week_high) / fifty_two_week_high) * 100
    
    if fifty_two_week_low:
        result['distance_from_52w_low'] = ((current_price - fifty_two_week_low) / fifty_two_week_low) * 100
    
    if fifty_two_week_high and fifty_two_week_low and fifty_two_week_high != fifty_two_week_low:
        result['position_in_52w_range'] = ((current_price - fifty_two_week_low) / 
                                           (fifty_two_week_high - fifty_two_week_low)) * 100
    
    return result


def calculate_sma_crossover(current_price: Optional[float],
                           fifty_day_average: Optional[float],
                           two_hundred_day_average: Optional[float]) -> Dict[str, Any]:
    """
    Berechnet SMA50/200-Crossover Status und Abstände
    
    Returns:
        Dict mit sma50_distance, sma200_distance, golden_cross, death_cross, trend
    """
    result = {
        'distance_from_sma50': None,
        'distance_from_sma200': None,
        'golden_cross': None,  # SMA50 > SMA200 (bullish)
        'death_cross': None,   # SMA50 < SMA200 (bearish)
        'trend': None,         # 'bullish', 'bearish', 'neutral'
        'price_above_sma50': None,
        'price_above_sma200': None
    }
    
    if current_price and fifty_day_average:
        result['distance_from_sma50'] = ((current_price - fifty_day_average) / fifty_day_average) * 100
        result['price_above_sma50'] = current_price > fifty_day_average
    
    if current_price and two_hundred_day_average:
        result['distance_from_sma200'] = ((current_price - two_hundred_day_average) / two_hundred_day_average) * 100
        result['price_above_sma200'] = current_price > two_hundred_day_average
    
    if fifty_day_average and two_hundred_day_average:
        result['golden_cross'] = fifty_day_average > two_hundred_day_average
        result['death_cross'] = fifty_day_average < two_hundred_day_average
        
        # Trend bestimmen
        if result['golden_cross']:
            result['trend'] = 'bullish'
        elif result['death_cross']:
            result['trend'] = 'bearish'
        else:
            result['trend'] = 'neutral'
    
    return result


def calculate_relative_volume(volume: Optional[int],
                              average_volume: Optional[int]) -> Dict[str, Optional[float]]:
    """
    Berechnet relatives Volumen
    
    Returns:
        Dict mit relative_volume, volume_ratio_category
    """
    result = {
        'relative_volume': None,
        'volume_ratio': None,
        'volume_category': None  # 'very_low', 'low', 'normal', 'high', 'very_high'
    }
    
    if volume and average_volume and average_volume > 0:
        ratio = volume / average_volume
        result['relative_volume'] = ratio
        result['volume_ratio'] = ratio
        
        # Kategorisierung
        if ratio < 0.5:
            result['volume_category'] = 'very_low'
        elif ratio < 0.8:
            result['volume_category'] = 'low'
        elif ratio < 1.2:
            result['volume_category'] = 'normal'
        elif ratio < 2.0:
            result['volume_category'] = 'high'
        else:
            result['volume_category'] = 'very_high'
    
    return result


def calculate_free_cashflow_yield(free_cashflow: Optional[float],
                                  market_cap: Optional[float]) -> Optional[float]:
    """
    Berechnet Free Cashflow Yield
    
    Returns:
        FCF Yield in Prozent
    """
    if free_cashflow and market_cap and market_cap > 0:
        return (free_cashflow / market_cap) * 100
    return None


def detect_sma_crossovers(historical_prices: pd.DataFrame, 
                          sma_short: int = 50, 
                          sma_long: int = 200,
                          lookback_days: int = 365) -> Dict[str, Any]:
    """
    Detektiert Golden Cross und Death Cross Events in historischen Daten
    
    Golden Cross: SMA50 kreuzt SMA200 von unten nach oben (bullish)
    Death Cross: SMA50 kreuzt SMA200 von oben nach unten (bearish)
    
    Args:
        historical_prices: DataFrame mit 'Close' Spalte
        sma_short: Periode für kurzen SMA (default: 50)
        sma_long: Periode für langen SMA (default: 200)
        lookback_days: Wie weit zurückschauen (default: 365 Tage)
    
    Returns:
        Dict mit:
        - last_crossover_type: 'golden_cross', 'death_cross', oder None
        - last_crossover_date: ISO-Format Datum oder None
        - days_since_crossover: Anzahl Tage seit letztem Crossover
        - price_at_crossover: Preis beim Crossover
        - current_price: Aktueller Preis
        - price_change_since_crossover: Prozentuale Änderung seit Crossover
        - all_crossovers: Liste aller Crossovers im Zeitraum
    """
    result = {
        'last_crossover_type': None,
        'last_crossover_date': None,
        'days_since_crossover': None,
        'price_at_crossover': None,
        'current_price': None,
        'price_change_since_crossover': None,
        'all_crossovers': []
    }
    
    if historical_prices is None or historical_prices.empty or 'Close' not in historical_prices.columns:
        return result
    
    try:
        # Kopie erstellen um Original nicht zu verändern
        df = historical_prices.copy()
        
        # SMAs berechnen
        df[f'SMA{sma_short}'] = df['Close'].rolling(window=sma_short).mean()
        df[f'SMA{sma_long}'] = df['Close'].rolling(window=sma_long).mean()
        
        # NaN-Werte entfernen (erste 200 Tage haben keine vollständigen SMAs)
        df = df.dropna(subset=[f'SMA{sma_short}', f'SMA{sma_long}'])
        
        if len(df) < 2:
            return result
        
        # Nur die letzten lookback_days betrachten
        if len(df) > lookback_days:
            df = df.tail(lookback_days)
        
        # Crossover-Detection: Vergleiche vorherigen Tag mit aktuellem Tag
        df['SMA_diff'] = df[f'SMA{sma_short}'] - df[f'SMA{sma_long}']
        df['SMA_diff_prev'] = df['SMA_diff'].shift(1)
        
        # Golden Cross: SMA_diff wechselt von negativ zu positiv
        df['golden_cross'] = (df['SMA_diff_prev'] < 0) & (df['SMA_diff'] > 0)
        
        # Death Cross: SMA_diff wechselt von positiv zu negativ
        df['death_cross'] = (df['SMA_diff_prev'] > 0) & (df['SMA_diff'] < 0)
        
        # Alle Crossovers sammeln
        crossovers = []
        
        for idx, row in df.iterrows():
            if row['golden_cross']:
                crossovers.append({
                    'type': 'golden_cross',
                    'date': idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx),
                    'price': float(row['Close']),
                    'sma_short': float(row[f'SMA{sma_short}']),
                    'sma_long': float(row[f'SMA{sma_long}'])
                })
            elif row['death_cross']:
                crossovers.append({
                    'type': 'death_cross',
                    'date': idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx),
                    'price': float(row['Close']),
                    'sma_short': float(row[f'SMA{sma_short}']),
                    'sma_long': float(row[f'SMA{sma_long}'])
                })
        
        result['all_crossovers'] = crossovers
        
        # Letzter Crossover (falls vorhanden)
        if crossovers:
            last_crossover = crossovers[-1]
            result['last_crossover_type'] = last_crossover['type']
            result['last_crossover_date'] = last_crossover['date']
            result['price_at_crossover'] = last_crossover['price']
            
            # Aktueller Preis
            current_price = float(df['Close'].iloc[-1])
            result['current_price'] = current_price
            
            # Tage seit Crossover
            try:
                crossover_date = pd.to_datetime(last_crossover['date'])
                last_date = df.index[-1]
                days_diff = (last_date - crossover_date).days
                result['days_since_crossover'] = days_diff
            except Exception as e:
                logger.warning(f"Fehler bei Berechnung days_since_crossover: {e}")
            
            # Performance seit Crossover
            if result['price_at_crossover'] and result['price_at_crossover'] > 0:
                price_change = ((current_price - result['price_at_crossover']) / result['price_at_crossover']) * 100
                result['price_change_since_crossover'] = price_change
        
        logger.info(f"SMA Crossover Detection: Gefunden {len(crossovers)} Crossovers, letzter: {result['last_crossover_type']}")
        
    except Exception as e:
        logger.error(f"Fehler bei SMA Crossover Detection: {str(e)}")
    
    return result


def calculate_fibonacci_levels(historical_prices: List[float], 
                               period_days: Optional[int] = None) -> Optional[Dict]:
    """
    Berechnet Fibonacci Retracement und Extension Levels
    
    Args:
        historical_prices: Liste historischer Preise
        period_days: Anzahl der Tage für Swing High/Low (None = alle verfügbaren)
    
    Returns:
        Dict mit Fibonacci Levels oder None
    """
    if not historical_prices or len(historical_prices) < 10:
        return None
    
    try:
        # Zeitraum bestimmen
        if period_days and len(historical_prices) > period_days:
            data = historical_prices[-period_days:]
        else:
            data = historical_prices
        
        # Swing High und Low finden
        swing_high = max(data)
        swing_low = min(data)
        range_value = swing_high - swing_low
        
        if range_value == 0:
            return None
        
        # Fibonacci Retracement Levels (von Hoch nach Tief)
        retracement_levels = {
            "0.0": swing_low,
            "23.6": swing_high - (range_value * 0.236),
            "38.2": swing_high - (range_value * 0.382),
            "50.0": swing_high - (range_value * 0.5),
            "61.8": swing_high - (range_value * 0.618),
            "78.6": swing_high - (range_value * 0.786),
            "100.0": swing_high
        }
        
        # Fibonacci Extension Levels (für Ziele nach oben)
        extension_levels = {
            "0.0": swing_low,
            "100.0": swing_high,
            "127.2": swing_low + (range_value * 1.272),
            "161.8": swing_low + (range_value * 1.618),
            "200.0": swing_low + (range_value * 2.0),
            "261.8": swing_low + (range_value * 2.618)
        }
        
        return {
            "swing_high": swing_high,
            "swing_low": swing_low,
            "range": range_value,
            "retracement": retracement_levels,
            "extension": extension_levels
        }
        
    except Exception as e:
        logger.error(f"Fehler bei Fibonacci Berechnung: {str(e)}")
        return None


def find_support_resistance(historical_prices: List[float], 
                            window: int = 5, 
                            tolerance: float = 0.02,
                            max_levels: int = 3) -> Optional[Dict]:
    """
    Findet Support und Resistance Levels basierend auf lokalen Hochs/Tiefs
    
    Args:
        historical_prices: Liste historischer Preise
        window: Fenster für lokale Hoch/Tief Erkennung (Standard: 5)
        tolerance: Prozent-Toleranz für Clustering (Standard: 0.02 = 2%)
        max_levels: Max. Anzahl der stärksten Levels (Standard: 3)
    
    Returns:
        Dict mit Support/Resistance Levels oder None
    """
    if not historical_prices or len(historical_prices) < (window * 2 + 1):
        return None
    
    try:
        levels = []
        current_price = historical_prices[-1]
        
        # Finde lokale Hochs und Tiefs
        for i in range(window, len(historical_prices) - window):
            price = historical_prices[i]
            
            # Lokales Hoch (Resistance)?
            is_local_high = all(price >= historical_prices[i-j] for j in range(1, window+1)) and \
                           all(price >= historical_prices[i+j] for j in range(1, window+1))
            
            # Lokales Tief (Support)?
            is_local_low = all(price <= historical_prices[i-j] for j in range(1, window+1)) and \
                          all(price <= historical_prices[i+j] for j in range(1, window+1))
            
            if is_local_high:
                levels.append({"price": price, "type": "resistance", "index": i})
            elif is_local_low:
                levels.append({"price": price, "type": "support", "index": i})
        
        if not levels:
            return None
        
        # Clustering: Ähnliche Levels zusammenfassen
        clustered_levels = []
        levels_sorted = sorted(levels, key=lambda x: x['price'])
        
        i = 0
        while i < len(levels_sorted):
            cluster = [levels_sorted[i]]
            j = i + 1
            
            # Sammle alle Levels innerhalb der Toleranz
            while j < len(levels_sorted):
                if abs(levels_sorted[j]['price'] - cluster[0]['price']) / cluster[0]['price'] <= tolerance:
                    cluster.append(levels_sorted[j])
                    j += 1
                else:
                    break
            
            # Berechne Durchschnitt und Stärke des Clusters
            avg_price = sum(l['price'] for l in cluster) / len(cluster)
            strength = len(cluster)  # Wie oft wurde dieses Level getestet
            level_type = max(set(l['type'] for l in cluster), key=lambda x: sum(1 for l in cluster if l['type'] == x))
            
            # Berechne Relevanz (Nähe zum aktuellen Preis)
            distance_percent = abs(avg_price - current_price) / current_price
            relevance_score = 1.0 / (1.0 + distance_percent * 10)  # Je näher, desto relevanter
            
            # Gesamtscore: 60% Stärke, 40% Relevanz
            total_score = (strength * 0.6) + (relevance_score * strength * 0.4)
            
            clustered_levels.append({
                "price": avg_price,
                "type": level_type,
                "strength": strength,
                "relevance": relevance_score,
                "score": total_score
            })
            
            i = j
        
        # Sortiere nach Score und nimm die Top N
        clustered_levels.sort(key=lambda x: x['score'], reverse=True)
        top_levels = clustered_levels[:max_levels]
        
        # Trenne in Support und Resistance
        support_levels = [l for l in top_levels if l['type'] == 'support']
        resistance_levels = [l for l in top_levels if l['type'] == 'resistance']
        
        return {
            "support": support_levels,
            "resistance": resistance_levels,
            "current_price": current_price
        }
        
    except Exception as e:
        logger.error(f"Fehler bei Support/Resistance Berechnung: {str(e)}")
        return None


# ============================================================================
# PHASE 2: BEWERTUNGS-SCORES
# ============================================================================

def calculate_peg_ratio(pe_ratio: Optional[float],
                       earnings_growth: Optional[float]) -> Optional[float]:
    """
    Berechnet PEG Ratio falls nicht vorhanden
    
    Returns:
        PEG Ratio
    """
    if pe_ratio and earnings_growth and earnings_growth > 0:
        # Earnings growth is usually in decimal (0.15 = 15%)
        growth_percent = earnings_growth * 100 if earnings_growth < 1 else earnings_growth
        return pe_ratio / growth_percent
    return None


def calculate_value_score(pe_ratio: Optional[float],
                         price_to_book: Optional[float],
                         price_to_sales: Optional[float],
                         industry_avg_pe: Optional[float] = None,
                         industry_avg_pb: Optional[float] = None,
                         industry_avg_ps: Optional[float] = None) -> Dict[str, Optional[float]]:
    """
    Berechnet Value Score (0-100, höher = besser bewertet/günstiger)
    
    Logik: Niedrigere Ratios = höherer Score
    """
    result = {
        'value_score': None,
        'pe_score': None,
        'pb_score': None,
        'ps_score': None,
        'value_category': None  # 'undervalued', 'fair', 'overvalued'
    }
    
    scores = []
    
    # PE Score (inverse Bewertung)
    if pe_ratio and pe_ratio > 0:
        if industry_avg_pe and industry_avg_pe > 0:
            # Relative zum Branchendurchschnitt
            pe_score = max(0, min(100, 100 - ((pe_ratio / industry_avg_pe - 1) * 100)))
        else:
            # Absolute Bewertung (unter 15 = gut, über 30 = teuer)
            pe_score = max(0, min(100, (30 - pe_ratio) / 30 * 100))
        
        result['pe_score'] = pe_score
        scores.append(pe_score)
    
    # PB Score
    if price_to_book and price_to_book > 0:
        if industry_avg_pb and industry_avg_pb > 0:
            pb_score = max(0, min(100, 100 - ((price_to_book / industry_avg_pb - 1) * 100)))
        else:
            # Unter 1 = sehr gut, über 3 = teuer
            pb_score = max(0, min(100, (3 - price_to_book) / 3 * 100))
        
        result['pb_score'] = pb_score
        scores.append(pb_score)
    
    # PS Score
    if price_to_sales and price_to_sales > 0:
        if industry_avg_ps and industry_avg_ps > 0:
            ps_score = max(0, min(100, 100 - ((price_to_sales / industry_avg_ps - 1) * 100)))
        else:
            # Unter 1 = sehr gut, über 5 = teuer
            ps_score = max(0, min(100, (5 - price_to_sales) / 5 * 100))
        
        result['ps_score'] = ps_score
        scores.append(ps_score)
    
    # Gesamtscore
    if scores:
        value_score = sum(scores) / len(scores)
        result['value_score'] = value_score
        
        # Kategorisierung
        if value_score >= 70:
            result['value_category'] = 'undervalued'
        elif value_score >= 40:
            result['value_category'] = 'fair'
        else:
            result['value_category'] = 'overvalued'
    
    return result


def calculate_quality_score(return_on_equity: Optional[float],
                           return_on_assets: Optional[float],
                           profit_margins: Optional[float],
                           operating_margins: Optional[float],
                           debt_to_equity: Optional[float]) -> Dict[str, Optional[float]]:
    """
    Berechnet Quality Score (0-100, höher = bessere Qualität)
    """
    result = {
        'quality_score': None,
        'roe_score': None,
        'roa_score': None,
        'profitability_score': None,
        'financial_health_score': None,
        'quality_category': None  # 'excellent', 'good', 'average', 'poor'
    }
    
    scores = []
    
    # ROE Score (über 15% = gut)
    if return_on_equity:
        roe_percent = return_on_equity * 100 if return_on_equity < 1 else return_on_equity
        roe_score = min(100, (roe_percent / 20) * 100)
        result['roe_score'] = roe_score
        scores.append(roe_score)
    
    # ROA Score (über 10% = gut)
    if return_on_assets:
        roa_percent = return_on_assets * 100 if return_on_assets < 1 else return_on_assets
        roa_score = min(100, (roa_percent / 15) * 100)
        result['roa_score'] = roa_score
        scores.append(roa_score)
    
    # Profitability Score (Kombination aus Profit und Operating Margins)
    profitability_scores = []
    if profit_margins:
        pm_percent = profit_margins * 100 if profit_margins < 1 else profit_margins
        profitability_scores.append(min(100, (pm_percent / 20) * 100))
    
    if operating_margins:
        om_percent = operating_margins * 100 if operating_margins < 1 else operating_margins
        profitability_scores.append(min(100, (om_percent / 25) * 100))
    
    if profitability_scores:
        profitability_score = sum(profitability_scores) / len(profitability_scores)
        result['profitability_score'] = profitability_score
        scores.append(profitability_score)
    
    # Financial Health Score (niedriger Debt-to-Equity = besser)
    if debt_to_equity is not None:
        if debt_to_equity < 0.5:
            financial_health = 100
        elif debt_to_equity < 1.0:
            financial_health = 80
        elif debt_to_equity < 2.0:
            financial_health = 60
        else:
            financial_health = max(0, 100 - ((debt_to_equity - 2) * 20))
        
        result['financial_health_score'] = financial_health
        scores.append(financial_health)
    
    # Gesamtscore
    if scores:
        quality_score = sum(scores) / len(scores)
        result['quality_score'] = quality_score
        
        # Kategorisierung
        if quality_score >= 80:
            result['quality_category'] = 'excellent'
        elif quality_score >= 60:
            result['quality_category'] = 'good'
        elif quality_score >= 40:
            result['quality_category'] = 'average'
        else:
            result['quality_category'] = 'poor'
    
    return result


def calculate_dividend_safety_score(dividend_yield: Optional[float],
                                   payout_ratio: Optional[float],
                                   free_cashflow: Optional[float],
                                   dividend_rate: Optional[float],
                                   five_year_avg_dividend_yield: Optional[float]) -> Dict[str, Optional[float]]:
    """
    Berechnet Dividend Safety Score (0-100, höher = sicherer)
    """
    result = {
        'dividend_safety_score': None,
        'payout_sustainability': None,
        'yield_sustainability': None,
        'dividend_growth_potential': None,
        'safety_category': None  # 'very_safe', 'safe', 'moderate', 'risky', 'very_risky'
    }
    
    scores = []
    
    # Payout Ratio Score (unter 60% = gut)
    if payout_ratio is not None:
        pr_percent = payout_ratio * 100 if payout_ratio < 1 else payout_ratio
        if pr_percent < 40:
            payout_score = 100
        elif pr_percent < 60:
            payout_score = 80
        elif pr_percent < 80:
            payout_score = 60
        else:
            payout_score = max(0, 100 - pr_percent)
        
        result['payout_sustainability'] = payout_score
        scores.append(payout_score)
    
    # Yield Sustainability (Vergleich mit 5-Jahres-Durchschnitt)
    if dividend_yield and five_year_avg_dividend_yield and five_year_avg_dividend_yield > 0:
        dy_percent = dividend_yield * 100 if dividend_yield < 1 else dividend_yield
        avg_dy_percent = five_year_avg_dividend_yield * 100 if five_year_avg_dividend_yield < 1 else five_year_avg_dividend_yield
        
        ratio = dy_percent / avg_dy_percent
        if 0.8 <= ratio <= 1.2:
            yield_score = 100  # Stabil
        elif 0.6 <= ratio <= 1.4:
            yield_score = 80   # Leicht schwankend
        else:
            yield_score = 60   # Stark schwankend
        
        result['yield_sustainability'] = yield_score
        scores.append(yield_score)
    
    # Dividend Growth Potential (basiert auf FCF Coverage)
    if free_cashflow and dividend_rate and dividend_rate > 0:
        fcf_coverage = free_cashflow / dividend_rate if dividend_rate != 0 else 0
        if fcf_coverage > 2:
            growth_score = 100
        elif fcf_coverage > 1.5:
            growth_score = 80
        elif fcf_coverage > 1:
            growth_score = 60
        else:
            growth_score = 40
        
        result['dividend_growth_potential'] = growth_score
        scores.append(growth_score)
    
    # Gesamtscore
    if scores:
        safety_score = sum(scores) / len(scores)
        result['dividend_safety_score'] = safety_score
        
        # Kategorisierung
        if safety_score >= 85:
            result['safety_category'] = 'very_safe'
        elif safety_score >= 70:
            result['safety_category'] = 'safe'
        elif safety_score >= 50:
            result['safety_category'] = 'moderate'
        elif safety_score >= 30:
            result['safety_category'] = 'risky'
        else:
            result['safety_category'] = 'very_risky'
    
    return result


# ============================================================================
# PHASE 3: ERWEITERTE ANALYSE
# ============================================================================

def calculate_macd(close_prices: pd.Series, 
                  fast_period: int = 12,
                  slow_period: int = 26,
                  signal_period: int = 9) -> Dict[str, Optional[float]]:
    """
    Berechnet MACD (Moving Average Convergence Divergence)
    
    Returns:
        Dict mit macd_line, signal_line, histogram, trend
    """
    result = {
        'macd_line': None,
        'signal_line': None,
        'histogram': None,
        'trend': None  # 'bullish', 'bearish', 'neutral'
    }
    
    if close_prices is None or len(close_prices) < slow_period + signal_period:
        return result
    
    try:
        # EMA berechnen
        ema_fast = close_prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = close_prices.ewm(span=slow_period, adjust=False).mean()
        
        # MACD Line
        macd_line = ema_fast - ema_slow
        
        # Signal Line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # Histogram
        histogram = macd_line - signal_line
        
        # Aktuelle Werte
        result['macd_line'] = float(macd_line.iloc[-1])
        result['signal_line'] = float(signal_line.iloc[-1])
        result['histogram'] = float(histogram.iloc[-1])
        
        # Trend bestimmen
        if result['histogram'] > 0 and result['macd_line'] > result['signal_line']:
            result['trend'] = 'bullish'
        elif result['histogram'] < 0 and result['macd_line'] < result['signal_line']:
            result['trend'] = 'bearish'
        else:
            result['trend'] = 'neutral'
        
    except Exception as e:
        logger.error(f"Error calculating MACD: {e}")
    
    return result


def calculate_stochastic_oscillator(high_prices: pd.Series,
                                   low_prices: pd.Series,
                                   close_prices: pd.Series,
                                   period: int = 14,
                                   smooth_k: int = 3,
                                   smooth_d: int = 3) -> Dict[str, Optional[float]]:
    """
    Berechnet Stochastic Oscillator
    
    Returns:
        Dict mit k_percent, d_percent, signal, overbought, oversold
    """
    result = {
        'k_percent': None,
        'd_percent': None,
        'signal': None,  # 'overbought', 'oversold', 'neutral'
        'is_overbought': False,
        'is_oversold': False
    }
    
    if (high_prices is None or low_prices is None or close_prices is None or 
        len(close_prices) < period):
        return result
    
    try:
        # Lowest low und highest high über period
        lowest_low = low_prices.rolling(window=period).min()
        highest_high = high_prices.rolling(window=period).max()
        
        # %K berechnen
        k_percent = 100 * ((close_prices - lowest_low) / (highest_high - lowest_low))
        
        # %K smoothing
        if smooth_k > 1:
            k_percent = k_percent.rolling(window=smooth_k).mean()
        
        # %D (Signal Line)
        d_percent = k_percent.rolling(window=smooth_d).mean()
        
        # Aktuelle Werte
        result['k_percent'] = float(k_percent.iloc[-1])
        result['d_percent'] = float(d_percent.iloc[-1])
        
        # Signale
        if result['k_percent'] >= 80:
            result['signal'] = 'overbought'
            result['is_overbought'] = True
        elif result['k_percent'] <= 20:
            result['signal'] = 'oversold'
            result['is_oversold'] = True
        else:
            result['signal'] = 'neutral'
        
    except Exception as e:
        logger.error(f"Error calculating Stochastic Oscillator: {e}")
    
    return result


def calculate_atr(high_prices: pd.Series,
                  low_prices: pd.Series,
                  close_prices: pd.Series,
                  period: int = 14) -> Dict[str, Any]:
    """
    Berechnet Average True Range (ATR) für Volatilitätsmessung und Stop-Loss-Platzierung
    
    Args:
        high_prices: High prices
        low_prices: Low prices
        close_prices: Close prices
        period: ATR period (default: 14)
        
    Returns:
        Dict mit:
        - atr_current: Aktueller ATR-Wert
        - atr_percentage: ATR als % vom aktuellen Preis
        - stop_loss_conservative: Aktueller Preis - 1.5x ATR
        - stop_loss_standard: Aktueller Preis - 2x ATR
        - stop_loss_aggressive: Aktueller Preis - 3x ATR
        - take_profit_conservative: Aktueller Preis + 2x ATR
        - take_profit_standard: Aktueller Preis + 3x ATR
        - take_profit_aggressive: Aktueller Preis + 4x ATR
        - volatility_rating: 'low', 'moderate', 'high', 'very_high'
    """
    result = {
        'atr_current': None,
        'atr_percentage': None,
        'stop_loss_conservative': None,
        'stop_loss_standard': None,
        'stop_loss_aggressive': None,
        'take_profit_conservative': None,
        'take_profit_standard': None,
        'take_profit_aggressive': None,
        'volatility_rating': None,
        'risk_reward_ratio': None  # Standard 2x ATR Stop vs 3x ATR Target = 1:1.5
    }
    
    if (high_prices is None or low_prices is None or close_prices is None or 
        len(close_prices) < period + 1):
        return result
    
    try:
        # True Range berechnen
        # TR = max(high - low, abs(high - prev_close), abs(low - prev_close))
        high_low = high_prices - low_prices
        high_close = abs(high_prices - close_prices.shift())
        low_close = abs(low_prices - close_prices.shift())
        
        # Maximum der drei Werte
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # ATR = Exponential Moving Average von True Range
        atr = true_range.ewm(span=period, adjust=False).mean()
        
        # Aktuelle Werte
        current_price = close_prices.iloc[-1]
        current_atr = atr.iloc[-1]
        
        result['atr_current'] = float(current_atr)
        result['atr_percentage'] = float((current_atr / current_price) * 100)
        
        # Stop-Loss Levels (unter dem aktuellen Preis für Long-Positionen)
        result['stop_loss_conservative'] = float(current_price - (1.5 * current_atr))
        result['stop_loss_standard'] = float(current_price - (2.0 * current_atr))
        result['stop_loss_aggressive'] = float(current_price - (3.0 * current_atr))
        
        # Take-Profit Levels (über dem aktuellen Preis)
        result['take_profit_conservative'] = float(current_price + (2.0 * current_atr))
        result['take_profit_standard'] = float(current_price + (3.0 * current_atr))
        result['take_profit_aggressive'] = float(current_price + (4.0 * current_atr))
        
        # Risk/Reward Ratio (Standard: 2x ATR Stop vs 3x ATR Target)
        stop_distance = 2.0 * current_atr
        target_distance = 3.0 * current_atr
        result['risk_reward_ratio'] = float(target_distance / stop_distance)
        
        # Volatility Rating basierend auf ATR als Prozentsatz
        atr_pct = result['atr_percentage']
        if atr_pct < 2:
            result['volatility_rating'] = 'low'
        elif atr_pct < 4:
            result['volatility_rating'] = 'moderate'
        elif atr_pct < 6:
            result['volatility_rating'] = 'high'
        else:
            result['volatility_rating'] = 'very_high'
        
    except Exception as e:
        logger.error(f"Error calculating ATR: {e}")
    
    return result


def calculate_volatility_metrics(close_prices: pd.Series) -> Dict[str, Optional[float]]:
    """
    Berechnet Volatilitäts-Metriken für verschiedene Zeiträume
    
    Returns:
        Dict mit volatility_30d, volatility_90d, volatility_1y (annualisiert)
    """
    result = {
        'volatility_30d': None,
        'volatility_90d': None,
        'volatility_1y': None,
        'volatility_category': None  # 'very_low', 'low', 'moderate', 'high', 'very_high'
    }
    
    if close_prices is None or len(close_prices) < 30:
        return result
    
    try:
        # Returns berechnen
        returns = close_prices.pct_change().dropna()
        
        # 30-Tage Volatilität (annualisiert)
        if len(returns) >= 30:
            vol_30d = returns.tail(30).std() * np.sqrt(252) * 100
            result['volatility_30d'] = float(vol_30d)
        
        # 90-Tage Volatilität
        if len(returns) >= 90:
            vol_90d = returns.tail(90).std() * np.sqrt(252) * 100
            result['volatility_90d'] = float(vol_90d)
        
        # 1-Jahr Volatilität
        if len(returns) >= 252:
            vol_1y = returns.tail(252).std() * np.sqrt(252) * 100
            result['volatility_1y'] = float(vol_1y)
        
        # Kategorisierung basierend auf 30d Volatilität
        if result['volatility_30d']:
            vol = result['volatility_30d']
            if vol < 15:
                result['volatility_category'] = 'very_low'
            elif vol < 25:
                result['volatility_category'] = 'low'
            elif vol < 40:
                result['volatility_category'] = 'moderate'
            elif vol < 60:
                result['volatility_category'] = 'high'
            else:
                result['volatility_category'] = 'very_high'
        
    except Exception as e:
        logger.error(f"Error calculating volatility metrics: {e}")
    
    return result


def calculate_maximum_drawdown(close_prices: pd.Series) -> Dict[str, Optional[float]]:
    """
    Berechnet Maximum Drawdown
    
    Returns:
        Dict mit max_drawdown (in Prozent), max_drawdown_duration (in Tagen)
    """
    result = {
        'max_drawdown': None,
        'max_drawdown_duration': None,
        'current_drawdown': None
    }
    
    if close_prices is None or len(close_prices) < 2:
        return result
    
    try:
        # Kumulatives Maximum
        cummax = close_prices.cummax()
        
        # Drawdown berechnen
        drawdown = (close_prices - cummax) / cummax * 100
        
        # Maximum Drawdown
        result['max_drawdown'] = float(drawdown.min())
        
        # Aktueller Drawdown
        result['current_drawdown'] = float(drawdown.iloc[-1])
        
        # Duration (vereinfachte Berechnung)
        if result['max_drawdown'] < 0:
            max_dd_idx = drawdown.idxmin()
            # Finde vorheriges High
            pre_dd_high = cummax.loc[:max_dd_idx].idxmax()
            result['max_drawdown_duration'] = (max_dd_idx - pre_dd_high).days if hasattr(max_dd_idx, 'days') else None
        
    except Exception as e:
        logger.error(f"Error calculating maximum drawdown: {e}")
    
    return result


def calculate_analyst_metrics(price_targets: Optional[Dict[str, float]],
                             current_price: Optional[float],
                             recommendations: Optional[list]) -> Dict[str, Any]:
    """
    Berechnet Analystendaten-Metriken
    
    Returns:
        Dict mit upside_potential, consensus_strength, rating_summary
    """
    result = {
        'upside_potential': None,
        'target_mean': None,
        'target_high': None,
        'target_low': None,
        'consensus_strength': None,  # Wie einig sind sich die Analysten
        'recommendation_score': None,  # 1-5 (1=Strong Buy, 5=Sell)
        'number_of_analysts': None
    }
    
    # Upside Potential
    if price_targets and current_price:
        mean_target = price_targets.get('mean')
        if mean_target and current_price > 0:
            result['upside_potential'] = ((mean_target - current_price) / current_price) * 100
            result['target_mean'] = mean_target
        
        result['target_high'] = price_targets.get('high')
        result['target_low'] = price_targets.get('low')
    
    # Consensus Strength (Standardabweichung der Kursziele)
    if price_targets:
        high = price_targets.get('high')
        low = price_targets.get('low')
        mean = price_targets.get('mean')
        
        if high and low and mean and mean > 0:
            # Einfache Measure: Range relativ zum Mean
            target_range = ((high - low) / mean) * 100
            
            if target_range < 20:
                result['consensus_strength'] = 'strong'
            elif target_range < 40:
                result['consensus_strength'] = 'moderate'
            else:
                result['consensus_strength'] = 'weak'
    
    # Recommendation Score (aus Recommendations-Liste)
    if recommendations:
        result['number_of_analysts'] = len(recommendations)
        
        # Vereinfachte Bewertung: Zähle Buy vs Sell Empfehlungen
        buy_count = sum(1 for r in recommendations if 'buy' in r.get('to_grade', '').lower())
        sell_count = sum(1 for r in recommendations if 'sell' in r.get('to_grade', '').lower())
        
        if buy_count > sell_count * 2:
            result['recommendation_score'] = 1.5  # Strong Buy
        elif buy_count > sell_count:
            result['recommendation_score'] = 2.0  # Buy
        elif sell_count > buy_count * 2:
            result['recommendation_score'] = 4.5  # Strong Sell
        elif sell_count > buy_count:
            result['recommendation_score'] = 4.0  # Sell
        else:
            result['recommendation_score'] = 3.0  # Hold
    
    return result


def calculate_beta_adjusted_metrics(close_prices: pd.Series,
                                   beta: Optional[float],
                                   risk_free_rate: float = 0.03,
                                   market_return: float = 0.10) -> Dict[str, Optional[float]]:
    """
    Berechnet Beta-adjustierte Risiko-Metriken
    
    Args:
        close_prices: Historische Schlusskurse
        beta: Beta-Wert der Aktie
        risk_free_rate: Risikofreier Zins (Standard: 3% = 0.03)
        market_return: Erwartete Marktrendite (Standard: 10% = 0.10)
        
    Returns:
        Dict mit Sharpe Ratio, Alpha, Treynor Ratio, Sortino Ratio, etc.
    """
    result = {
        'sharpe_ratio': None,
        'alpha': None,
        'treynor_ratio': None,
        'sortino_ratio': None,
        'beta_adjusted_return': None,
        'information_ratio': None,
        'downside_deviation': None,
        'total_return': None,
        'annualized_return': None,
        'risk_rating': None  # 'low', 'moderate', 'high', 'very_high'
    }
    
    if close_prices is None or len(close_prices) < 30:
        return result
    
    try:
        # Berechne Returns
        returns = close_prices.pct_change().dropna()
        
        if returns.empty:
            return result
        
        # Total Return und Annualized Return
        total_return = (close_prices.iloc[-1] / close_prices.iloc[0] - 1)
        days = len(close_prices)
        years = days / 252  # Trading days
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        result['total_return'] = float(total_return * 100)  # In Prozent
        result['annualized_return'] = float(annualized_return * 100)  # In Prozent
        
        # Volatilität (annualisiert)
        volatility = returns.std() * np.sqrt(252)
        
        # 1. SHARPE RATIO
        # Misst Überrendite pro Einheit Gesamtrisiko
        excess_return = annualized_return - risk_free_rate
        if volatility > 0:
            result['sharpe_ratio'] = float(excess_return / volatility)
        
        # 2. ALPHA (Jensen's Alpha)
        # Überrendite gegenüber CAPM-Erwartung
        if beta is not None:
            expected_return = risk_free_rate + beta * (market_return - risk_free_rate)
            result['alpha'] = float((annualized_return - expected_return) * 100)  # In Prozent
        
        # 3. TREYNOR RATIO
        # Überrendite pro Einheit systematisches Risiko (Beta)
        if beta is not None and beta > 0:
            result['treynor_ratio'] = float(excess_return / beta)
        
        # 4. DOWNSIDE DEVIATION
        # Nur negative Returns berücksichtigen
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0:
            downside_deviation = negative_returns.std() * np.sqrt(252)
            result['downside_deviation'] = float(downside_deviation * 100)  # In Prozent
            
            # 5. SORTINO RATIO
            # Wie Sharpe, aber nur Downside-Risiko
            if downside_deviation > 0:
                result['sortino_ratio'] = float(excess_return / downside_deviation)
        
        # 6. BETA-ADJUSTED RETURN
        # Normalisierte Rendite auf Beta = 1.0
        if beta is not None and beta > 0:
            result['beta_adjusted_return'] = float((annualized_return / beta) * 100)  # In Prozent
        
        # 7. INFORMATION RATIO
        # Konsistenz der Outperformance vs. Markt
        # Vereinfacht: Excess Return / Tracking Error
        excess_returns = returns - (market_return / 252)  # Daily market return
        tracking_error = excess_returns.std() * np.sqrt(252)
        if tracking_error > 0:
            result['information_ratio'] = float((annualized_return - market_return) / tracking_error)
        
        # 8. RISK RATING
        # Kombinierte Risikobewertung
        if result['sharpe_ratio'] is not None:
            sharpe = result['sharpe_ratio']
            if sharpe > 1.5:
                result['risk_rating'] = 'low'  # Sehr gutes Risk-Return-Verhältnis
            elif sharpe > 1.0:
                result['risk_rating'] = 'moderate'
            elif sharpe > 0.5:
                result['risk_rating'] = 'high'
            else:
                result['risk_rating'] = 'very_high'
        
    except Exception as e:
        logger.error(f"Error calculating beta-adjusted metrics: {e}")
    
    return result


def calculate_risk_adjusted_performance_score(sharpe_ratio: Optional[float],
                                             alpha: Optional[float],
                                             sortino_ratio: Optional[float],
                                             information_ratio: Optional[float]) -> Dict[str, Any]:
    """
    Berechnet einen kombinierten Risk-Adjusted Performance Score
    
    Returns:
        Dict mit overall_score, rating, individual_scores
    """
    result = {
        'overall_score': None,
        'rating': None,  # 'excellent', 'good', 'average', 'poor'
        'sharpe_contribution': None,
        'alpha_contribution': None,
        'sortino_contribution': None,
        'information_contribution': None
    }
    
    scores = []
    weights = []
    
    # Sharpe Ratio Score (Gewicht: 30%)
    if sharpe_ratio is not None:
        if sharpe_ratio > 2.0:
            sharpe_score = 100
        elif sharpe_ratio > 1.5:
            sharpe_score = 90
        elif sharpe_ratio > 1.0:
            sharpe_score = 75
        elif sharpe_ratio > 0.5:
            sharpe_score = 60
        elif sharpe_ratio > 0:
            sharpe_score = 40
        else:
            sharpe_score = 20
        
        result['sharpe_contribution'] = sharpe_score
        scores.append(sharpe_score)
        weights.append(0.30)
    
    # Alpha Score (Gewicht: 30%)
    if alpha is not None:
        if alpha > 5:
            alpha_score = 100
        elif alpha > 3:
            alpha_score = 85
        elif alpha > 1:
            alpha_score = 70
        elif alpha > 0:
            alpha_score = 55
        elif alpha > -2:
            alpha_score = 40
        else:
            alpha_score = 20
        
        result['alpha_contribution'] = alpha_score
        scores.append(alpha_score)
        weights.append(0.30)
    
    # Sortino Ratio Score (Gewicht: 25%)
    if sortino_ratio is not None:
        if sortino_ratio > 2.5:
            sortino_score = 100
        elif sortino_ratio > 2.0:
            sortino_score = 90
        elif sortino_ratio > 1.5:
            sortino_score = 75
        elif sortino_ratio > 1.0:
            sortino_score = 60
        elif sortino_ratio > 0.5:
            sortino_score = 45
        else:
            sortino_score = 25
        
        result['sortino_contribution'] = sortino_score
        scores.append(sortino_score)
        weights.append(0.25)
    
    # Information Ratio Score (Gewicht: 15%)
    if information_ratio is not None:
        if information_ratio > 1.0:
            ir_score = 100
        elif information_ratio > 0.75:
            ir_score = 85
        elif information_ratio > 0.5:
            ir_score = 70
        elif information_ratio > 0.25:
            ir_score = 55
        elif information_ratio > 0:
            ir_score = 40
        else:
            ir_score = 25
        
        result['information_contribution'] = ir_score
        scores.append(ir_score)
        weights.append(0.15)
    
    # Gewichteter Durchschnitt
    if scores:
        total_weight = sum(weights)
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0
        
        result['overall_score'] = float(overall_score)
        
        # Rating
        if overall_score >= 80:
            result['rating'] = 'excellent'
        elif overall_score >= 65:
            result['rating'] = 'good'
        elif overall_score >= 45:
            result['rating'] = 'average'
        else:
            result['rating'] = 'poor'
    
    return result


# ============================================================================
# HAUPTFUNKTION: Alle Metriken berechnen
# ============================================================================

def calculate_all_metrics(stock_data: Dict[str, Any], 
                         historical_prices: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Berechnet alle verfügbaren Metriken
    
    Args:
        stock_data: Dict mit allen verfügbaren Stock-Daten
        historical_prices: DataFrame mit historischen Preisdaten (optional)
        
    Returns:
        Dict mit allen berechneten Metriken, organisiert nach Phasen
    """
    result = {
        'basic_indicators': {},
        'valuation_scores': {},
        'advanced_analysis': {},
        'calculation_timestamp': datetime.now().isoformat()
    }
    
    # ========== PHASE 1 ==========
    
    # 52-Wochen Distanz - merge the dict into basic_indicators
    week_52_metrics = calculate_52week_distance(
        stock_data.get('current_price'),
        stock_data.get('fifty_two_week_high'),
        stock_data.get('fifty_two_week_low')
    )
    result['basic_indicators'].update(week_52_metrics)
    
    # SMA Crossover - merge the dict into basic_indicators
    sma_metrics = calculate_sma_crossover(
        stock_data.get('current_price'),
        stock_data.get('fifty_day_average'),
        stock_data.get('two_hundred_day_average')
    )
    result['basic_indicators'].update(sma_metrics)
    
    # Relative Volume - merge the dict into basic_indicators
    volume_metrics = calculate_relative_volume(
        stock_data.get('volume'),
        stock_data.get('average_volume')
    )
    result['basic_indicators'].update(volume_metrics)
    
    # Free Cashflow Yield
    result['basic_indicators']['fcf_yield'] = calculate_free_cashflow_yield(
        stock_data.get('free_cashflow'),
        stock_data.get('market_cap')
    )
    
    # SMA Crossover Detection (Golden Cross / Death Cross)
    if historical_prices is not None and not historical_prices.empty:
        crossover_data = detect_sma_crossovers(
            historical_prices,
            sma_short=50,
            sma_long=200,
            lookback_days=365
        )
        result['basic_indicators']['sma_crossovers'] = crossover_data
        
        # Fibonacci Levels (dynamisch abhängig vom Zeitraum)
        close_prices = historical_prices['Close'].tolist() if 'Close' in historical_prices.columns else None
        if close_prices:
            # Zeitraum basierend auf Datenumfang bestimmen
            period_days = len(close_prices) if len(close_prices) < 365 else None
            fibonacci_data = calculate_fibonacci_levels(close_prices, period_days)
            result['basic_indicators']['fibonacci_levels'] = fibonacci_data
            
            # Support & Resistance Levels
            support_resistance_data = find_support_resistance(
                close_prices,
                window=5,
                tolerance=0.02,
                max_levels=3
            )
            result['basic_indicators']['support_resistance'] = support_resistance_data
    
    # ========== PHASE 2 ==========
    
    # PEG Ratio
    result['valuation_scores']['peg_ratio'] = calculate_peg_ratio(
        stock_data.get('pe_ratio'),
        stock_data.get('earnings_growth')
    )
    
    # Value Score - merge the dict into valuation_scores
    value_metrics = calculate_value_score(
        stock_data.get('pe_ratio'),
        stock_data.get('price_to_book'),
        stock_data.get('price_to_sales')
    )
    result['valuation_scores'].update(value_metrics)
    
    # Quality Score - merge the dict into valuation_scores
    quality_metrics = calculate_quality_score(
        stock_data.get('return_on_equity'),
        stock_data.get('return_on_assets'),
        stock_data.get('profit_margins'),
        stock_data.get('operating_margins'),
        stock_data.get('debt_to_equity')
    )
    result['valuation_scores'].update(quality_metrics)
    
    # Dividend Safety Score - merge the dict into valuation_scores
    dividend_metrics = calculate_dividend_safety_score(
        stock_data.get('dividend_yield'),
        stock_data.get('payout_ratio'),
        stock_data.get('free_cashflow'),
        stock_data.get('dividend_rate'),
        stock_data.get('five_year_avg_dividend_yield')
    )
    result['valuation_scores'].update(dividend_metrics)
    
    # ========== PHASE 3 ==========
    
    if historical_prices is not None and not historical_prices.empty:
        # MACD - merge the dict into advanced_analysis
        if 'Close' in historical_prices.columns:
            macd_metrics = calculate_macd(
                historical_prices['Close']
            )
            result['advanced_analysis'].update(macd_metrics)
        
        # Stochastic Oscillator - merge the dict into advanced_analysis
        if all(col in historical_prices.columns for col in ['High', 'Low', 'Close']):
            stochastic_metrics = calculate_stochastic_oscillator(
                historical_prices['High'],
                historical_prices['Low'],
                historical_prices['Close']
            )
            result['advanced_analysis'].update(stochastic_metrics)
        
        # ATR (Average True Range) - merge the dict into advanced_analysis
        if all(col in historical_prices.columns for col in ['High', 'Low', 'Close']):
            atr_metrics = calculate_atr(
                historical_prices['High'],
                historical_prices['Low'],
                historical_prices['Close'],
                period=14
            )
            result['advanced_analysis'].update(atr_metrics)
        
        # Volatility Metrics - merge the dict into advanced_analysis
        if 'Close' in historical_prices.columns:
            volatility_metrics = calculate_volatility_metrics(
                historical_prices['Close']
            )
            result['advanced_analysis'].update(volatility_metrics)
            
            drawdown_metrics = calculate_maximum_drawdown(
                historical_prices['Close']
            )
            result['advanced_analysis'].update(drawdown_metrics)
            
            # Beta-Adjusted Metrics - merge the dict into advanced_analysis
            beta_adjusted = calculate_beta_adjusted_metrics(
                historical_prices['Close'],
                stock_data.get('beta'),
                risk_free_rate=0.03,  # 3% risikofreier Zins (anpassbar)
                market_return=0.10    # 10% erwartete Marktrendite (anpassbar)
            )
            result['advanced_analysis'].update(beta_adjusted)
            
            # Risk-Adjusted Performance Score - merge the dict into advanced_analysis
            risk_adjusted_perf = calculate_risk_adjusted_performance_score(
                beta_adjusted.get('sharpe_ratio'),
                beta_adjusted.get('alpha'),
                beta_adjusted.get('sortino_ratio'),
                beta_adjusted.get('information_ratio')
            )
            result['advanced_analysis'].update(risk_adjusted_perf)
    
    # Analyst Metrics - merge the dict into advanced_analysis
    analyst_metrics = calculate_analyst_metrics(
        stock_data.get('price_targets'),
        stock_data.get('current_price'),
        stock_data.get('recommendations')
    )
    result['advanced_analysis'].update(analyst_metrics)
    
    return result


# ============================================================================
# CHART-SPEZIFISCHE METRIKEN FÜR FRONTEND
# ============================================================================

def calculate_chart_metrics_for_display(ticker_symbol: str, period: str = "1y") -> Dict[str, Any]:
    """
    Berechnet Chart-spezifische Metriken für das Frontend
    Diese Funktion kombiniert historische Daten und berechnet Metriken,
    die im Chart-Tab des StockDetailModal angezeigt werden.
    
    Args:
        ticker_symbol: Stock ticker symbol
        period: Time period for calculations
        
    Returns:
        Dict mit allen Chart-relevanten Metriken:
        - RSI (current value + series)
        - MACD (current values + series)
        - Volatility (30d, 90d, 365d)
        - Moving Averages (SMA 50, 200)
        - Volume Analysis
        - Price Momentum (1M, 3M, 6M, 12M)
    """
    from backend.app.services.yfinance_service import get_chart_data, calculate_technical_indicators
    
    try:
        # Get chart data
        chart_data = get_chart_data(ticker_symbol, period=period, interval="1d")
        if not chart_data or not chart_data.get('close'):
            return {'error': 'No chart data available'}
        
        close_prices = pd.Series(chart_data['close'])
        dates = chart_data['dates']
        
        # Get technical indicators
        indicators = calculate_technical_indicators(
            ticker_symbol,
            period=period,
            indicators=['sma_50', 'sma_200', 'rsi', 'macd', 'volatility']
        )
        
        result = {
            'ticker': ticker_symbol,
            'period': period,
            'as_of_date': dates[-1] if dates else None,
            'metrics': {}
        }
        
        # ===== RSI =====
        if indicators and 'rsi' in indicators.get('indicators', {}):
            rsi_series = indicators['indicators']['rsi']
            # Get latest non-None RSI value
            rsi_current = None
            for val in reversed(rsi_series):
                if val is not None and not (isinstance(val, float) and val != val):
                    rsi_current = val
                    break
            
            result['metrics']['rsi'] = {
                'current': round(rsi_current, 2) if rsi_current else None,
                'signal': _interpret_rsi(rsi_current) if rsi_current else 'unknown',
                'description': 'Relative Strength Index (14-period)',
                'series': rsi_series  # Full series for chart
            }
        
        # ===== MACD =====
        if indicators and 'macd' in indicators.get('indicators', {}):
            macd_data = indicators['indicators']['macd']
            macd_series = macd_data['macd']
            signal_series = macd_data['signal']
            histogram_series = macd_data['histogram']
            
            # Get latest values
            macd_current = None
            signal_current = None
            histogram_current = None
            
            for val in reversed(macd_series):
                if val is not None and not (isinstance(val, float) and val != val):
                    macd_current = val
                    break
            for val in reversed(signal_series):
                if val is not None and not (isinstance(val, float) and val != val):
                    signal_current = val
                    break
            for val in reversed(histogram_series):
                if val is not None and not (isinstance(val, float) and val != val):
                    histogram_current = val
                    break
            
            result['metrics']['macd'] = {
                'macd_line': round(macd_current, 4) if macd_current else None,
                'signal_line': round(signal_current, 4) if signal_current else None,
                'histogram': round(histogram_current, 4) if histogram_current else None,
                'signal': _interpret_macd(histogram_current) if histogram_current else 'unknown',
                'description': 'Moving Average Convergence Divergence',
                'series': {
                    'macd': macd_series,
                    'signal': signal_series,
                    'histogram': histogram_series
                }
            }
        
        # ===== Volatility =====
        if indicators and 'volatility' in indicators.get('indicators', {}):
            vol_series = indicators['indicators']['volatility']
            vol_current = None
            for val in reversed(vol_series):
                if val is not None and not (isinstance(val, float) and val != val):
                    vol_current = val
                    break
            
            # Calculate different periods
            volatility_metrics = calculate_volatility_metrics(close_prices)
            
            result['metrics']['volatility'] = {
                'current_30d': round(vol_current, 2) if vol_current else None,
                'volatility_30d': volatility_metrics.get('volatility_30d'),
                'volatility_90d': volatility_metrics.get('volatility_90d'),
                'volatility_annual': volatility_metrics.get('volatility_annual'),
                'volatility_percentile': volatility_metrics.get('volatility_percentile'),
                'risk_category': volatility_metrics.get('risk_category'),
                'description': 'Historical Volatility (Annualized)',
                'series': vol_series
            }
        
        # ===== Moving Averages =====
        if indicators:
            sma_50 = None
            sma_200 = None
            
            if 'sma_50' in indicators.get('indicators', {}):
                sma_50_series = indicators['indicators']['sma_50']
                for val in reversed(sma_50_series):
                    if val is not None and not (isinstance(val, float) and val != val):
                        sma_50 = val
                        break
            
            if 'sma_200' in indicators.get('indicators', {}):
                sma_200_series = indicators['indicators']['sma_200']
                for val in reversed(sma_200_series):
                    if val is not None and not (isinstance(val, float) and val != val):
                        sma_200 = val
                        break
            
            current_price = close_prices.iloc[-1] if len(close_prices) > 0 else None
            
            result['metrics']['moving_averages'] = {
                'sma_50': round(sma_50, 2) if sma_50 else None,
                'sma_200': round(sma_200, 2) if sma_200 else None,
                'current_price': round(current_price, 2) if current_price else None,
                'golden_cross': sma_50 > sma_200 if (sma_50 and sma_200) else None,
                'price_vs_sma50': _compare_price_to_sma(current_price, sma_50),
                'price_vs_sma200': _compare_price_to_sma(current_price, sma_200),
                'description': 'Simple Moving Averages'
            }
        
        # ===== Price Momentum =====
        momentum_metrics = _calculate_price_momentum(close_prices, dates)
        result['metrics']['momentum'] = momentum_metrics
        
        # ===== Volume Analysis =====
        if 'volume' in chart_data:
            volume_series = pd.Series(chart_data['volume'])
            volume_metrics = _calculate_volume_metrics(volume_series)
            result['metrics']['volume'] = volume_metrics
        
        # ===== Maximum Drawdown =====
        drawdown_metrics = calculate_maximum_drawdown(close_prices)
        result['metrics']['drawdown'] = drawdown_metrics
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating chart metrics for {ticker_symbol}: {str(e)}")
        return {'error': str(e)}


def _interpret_rsi(rsi: float) -> str:
    """Interpret RSI value"""
    if rsi >= 70:
        return 'overbought'
    elif rsi <= 30:
        return 'oversold'
    elif rsi >= 60:
        return 'bullish'
    elif rsi <= 40:
        return 'bearish'
    else:
        return 'neutral'


def _interpret_macd(histogram: float) -> str:
    """Interpret MACD histogram"""
    if histogram > 0:
        return 'bullish'
    elif histogram < 0:
        return 'bearish'
    else:
        return 'neutral'


def _compare_price_to_sma(price: Optional[float], sma: Optional[float]) -> Dict[str, Any]:
    """Compare current price to SMA"""
    if not price or not sma:
        return {'above': None, 'distance_pct': None}
    
    distance_pct = ((price - sma) / sma) * 100
    return {
        'above': price > sma,
        'distance_pct': round(distance_pct, 2)
    }


def _calculate_price_momentum(prices: pd.Series, dates: list) -> Dict[str, Any]:
    """Calculate price momentum over different periods"""
    if len(prices) < 2:
        return {'error': 'Insufficient data'}
    
    current_price = prices.iloc[-1]
    result = {
        'current_price': round(current_price, 2),
        'momentum': {}
    }
    
    # Define periods in trading days
    periods = {
        '1M': 21,   # ~1 month
        '3M': 63,   # ~3 months
        '6M': 126,  # ~6 months
        '12M': 252  # ~12 months
    }
    
    for period_name, days in periods.items():
        if len(prices) > days:
            past_price = prices.iloc[-days]
            change_pct = ((current_price - past_price) / past_price) * 100
            result['momentum'][period_name] = {
                'change_pct': round(change_pct, 2),
                'past_price': round(past_price, 2),
                'signal': 'bullish' if change_pct > 0 else 'bearish'
            }
    
    return result


def _calculate_volume_metrics(volume: pd.Series) -> Dict[str, Any]:
    """Calculate volume-related metrics"""
    if len(volume) < 2:
        return {'error': 'Insufficient data'}
    
    current_volume = volume.iloc[-1]
    avg_volume = volume.mean()
    avg_volume_20d = volume.tail(20).mean() if len(volume) >= 20 else avg_volume
    
    return {
        'current_volume': int(current_volume),
        'average_volume': int(avg_volume),
        'average_volume_20d': int(avg_volume_20d),
        'relative_volume': round(current_volume / avg_volume, 2) if avg_volume > 0 else None,
        'volume_trend': 'above_average' if current_volume > avg_volume else 'below_average',
        'description': 'Volume Analysis'
    }
