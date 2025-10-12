"""
Technical Indicators Service
Provides calculations for technical analysis indicators including RSI, MACD, and divergence detection.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
import logging
from scipy.signal import argrelextrema

# Import base indicator functions from indicators_core.py
from backend.app.services.indicators_core import (
    calculate_rsi as core_calculate_rsi,
    calculate_macd as core_calculate_macd,
    calculate_bollinger_bands as core_calculate_bollinger_bands,
    calculate_sma as core_calculate_sma
)

logger = logging.getLogger(__name__)


# ============================================================================
# RSI (RELATIVE STRENGTH INDEX)
# ============================================================================

def calculate_rsi(close_prices: pd.Series, period: int = 14) -> Dict[str, Optional[float]]:
    """
    Calculate RSI (Relative Strength Index) using Wilder's smoothing method.
    
    Args:
        close_prices: Series of closing prices
        period: RSI period (default: 14)
        
    Returns:
        Dict with 'value', 'signal', 'series' (for charting)
    """
    result = {
        'value': None,
        'signal': None,  # 'overbought', 'oversold', 'bullish', 'bearish', 'neutral'
        'series': None
    }
    
    if close_prices is None or len(close_prices) < period + 1:
        return result
    
    try:
        # Use core_calculate_rsi for base calculation
        rsi_series = core_calculate_rsi(close_prices, period)
        if isinstance(rsi_series, pd.Series):
            current_rsi = rsi_series.iloc[-1]
            if pd.notna(current_rsi):
                result['value'] = float(current_rsi)
                result['signal'] = _interpret_rsi(current_rsi)
                result['series'] = rsi_series.tolist()
        elif isinstance(rsi_series, list) and len(rsi_series) > 0:
            current_rsi = rsi_series[-1]
            if current_rsi is not None:
                result['value'] = float(current_rsi)
                result['signal'] = _interpret_rsi(current_rsi)
                result['series'] = rsi_series
    except Exception as e:
        logger.error(f"Error calculating RSI: {e}")
    return result


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


def calculate_rsi_series(close_prices: pd.Series, period: int = 14) -> Optional[pd.Series]:
    """
    Calculate RSI as a pandas Series (for technical analysis charts).
    
    Args:
        close_prices: Series of closing prices
        period: RSI period (default: 14)
        
    Returns:
        Pandas Series of RSI values
    """
    try:
        # Use core_calculate_rsi for base calculation
        rsi_series = core_calculate_rsi(close_prices, period)
        if isinstance(rsi_series, pd.Series):
            return rsi_series
        elif isinstance(rsi_series, list):
            return pd.Series(rsi_series, index=close_prices.index)
        else:
            return None
    except Exception as e:
        logger.error(f"Error calculating RSI series: {e}")
        return None


# ============================================================================
# MACD (MOVING AVERAGE CONVERGENCE DIVERGENCE)
# ============================================================================

def calculate_macd(close_prices: pd.Series, 
                  fast_period: int = 12,
                  slow_period: int = 26,
                  signal_period: int = 9) -> Dict[str, Any]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        close_prices: Series of closing prices
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line EMA period (default: 9)
        
    Returns:
        Dict with macd_line, signal_line, histogram, trend, series
    """
    result = {
        'macd_line': None,
        'signal_line': None,
        'histogram': None,
        'trend': None,  # 'bullish', 'bearish', 'neutral'
        'series': None
    }
    
    if close_prices is None or len(close_prices) < slow_period + signal_period:
        return result
    
    try:
        # Use core_calculate_macd for base calculation
        macd_df = core_calculate_macd(close_prices, fast_period, slow_period, signal_period)
        if isinstance(macd_df, pd.DataFrame):
            macd_line = macd_df['macd'] if 'macd' in macd_df else macd_df.iloc[:,0]
            signal_line = macd_df['signal'] if 'signal' in macd_df else macd_df.iloc[:,1]
            histogram = macd_df['histogram'] if 'histogram' in macd_df else macd_df.iloc[:,2]
            result['macd_line'] = float(macd_line.iloc[-1])
            result['signal_line'] = float(signal_line.iloc[-1])
            result['histogram'] = float(histogram.iloc[-1])
            # Determine trend
            if result['histogram'] > 0 and result['macd_line'] > result['signal_line']:
                result['trend'] = 'bullish'
            elif result['histogram'] < 0 and result['macd_line'] < result['signal_line']:
                result['trend'] = 'bearish'
            else:
                result['trend'] = 'neutral'
            # Store series for charting
            result['series'] = {
                'macd': macd_line.tolist(),
                'signal': signal_line.tolist(),
                'histogram': histogram.tolist()
            }
        else:
            logger.error("core_calculate_macd did not return a DataFrame")
    except Exception as e:
        logger.error(f"Error calculating MACD: {e}")
    return result


def _interpret_macd(histogram: float) -> str:
    """Interpret MACD histogram"""
    if histogram > 0:
        return 'bullish'
    elif histogram < 0:
        return 'bearish'
    else:
        return 'neutral'


# ============================================================================
# DIVERGENCE DETECTION
# ============================================================================

def detect_price_peaks_and_troughs(prices: pd.Series, order: int = 5) -> Dict[str, List[Tuple[int, float]]]:
    """
    Detect local peaks (highs) and troughs (lows) in price data.
    
    Args:
        prices: Series of prices
        order: How many points on each side to use for comparison (default: 5)
        
    Returns:
        Dict with 'peaks' and 'troughs', each containing list of (index, value) tuples
    """
    try:
        # Find local maxima (peaks)
        peak_indices = argrelextrema(prices.values, np.greater, order=order)[0]
        peaks = [(int(idx), float(prices.iloc[idx])) for idx in peak_indices]
        
        # Find local minima (troughs)
        trough_indices = argrelextrema(prices.values, np.less, order=order)[0]
        troughs = [(int(idx), float(prices.iloc[idx])) for idx in trough_indices]
        
        return {
            'peaks': peaks,
            'troughs': troughs
        }
    except Exception as e:
        logger.error(f"Error detecting peaks and troughs: {e}")
        return {'peaks': [], 'troughs': []}


def detect_rsi_divergence(
    close_prices: pd.Series,
    rsi_series: pd.Series,
    lookback_days: int = 60,
    num_peaks: int = 3,
    min_peak_distance: int = 5
) -> Dict[str, Any]:
    """
    Detect RSI divergences (bullish and bearish).
    
    Bullish Divergence: Price makes lower lows, but RSI makes higher lows
    Bearish Divergence: Price makes higher highs, but RSI makes lower highs
    
    Args:
        close_prices: Series of closing prices
        rsi_series: Series of RSI values
        lookback_days: Number of days to look back (default: 60)
        num_peaks: Number of peaks to compare (default: 3)
        min_peak_distance: Minimum distance between peaks (default: 5)
        
    Returns:
        Dict with divergence information
    """
    result = {
        'bullish_divergence': False,
        'bearish_divergence': False,
        'bullish_divergence_points': [],
        'bearish_divergence_points': [],
        'signal': None,
        'confidence': None
    }
    
    if len(close_prices) < lookback_days or len(rsi_series) < lookback_days:
        return result
    
    try:
        # Use only the lookback period
        recent_prices = close_prices.iloc[-lookback_days:]
        recent_rsi = rsi_series.iloc[-lookback_days:]
        
        # Detect peaks and troughs
        price_extrema = detect_price_peaks_and_troughs(recent_prices, order=min_peak_distance)
        rsi_extrema = detect_price_peaks_and_troughs(recent_rsi, order=min_peak_distance)
        
        # Check for Bullish Divergence (compare troughs)
        if len(price_extrema['troughs']) >= num_peaks and len(rsi_extrema['troughs']) >= num_peaks:
            price_troughs = price_extrema['troughs'][-num_peaks:]
            rsi_troughs = rsi_extrema['troughs'][-num_peaks:]
            
            # Align troughs (find closest RSI trough for each price trough)
            aligned_troughs = _align_extrema(price_troughs, rsi_troughs, recent_prices.index, recent_rsi.index)
            
            if len(aligned_troughs) >= 2:
                # Check if price is making lower lows while RSI makes higher lows
                price_trend = _calculate_trend(aligned_troughs, 'price')
                rsi_trend = _calculate_trend(aligned_troughs, 'rsi')
                
                if price_trend == 'lower' and rsi_trend == 'higher':
                    result['bullish_divergence'] = True
                    result['bullish_divergence_points'] = aligned_troughs
                    result['signal'] = 'bullish'
                    result['confidence'] = _calculate_divergence_confidence(aligned_troughs)
        
        # Check for Bearish Divergence (compare peaks)
        if len(price_extrema['peaks']) >= num_peaks and len(rsi_extrema['peaks']) >= num_peaks:
            price_peaks = price_extrema['peaks'][-num_peaks:]
            rsi_peaks = rsi_extrema['peaks'][-num_peaks:]
            
            # Align peaks
            aligned_peaks = _align_extrema(price_peaks, rsi_peaks, recent_prices.index, recent_rsi.index)
            
            if len(aligned_peaks) >= 2:
                # Check if price is making higher highs while RSI makes lower highs
                price_trend = _calculate_trend(aligned_peaks, 'price')
                rsi_trend = _calculate_trend(aligned_peaks, 'rsi')
                
                if price_trend == 'higher' and rsi_trend == 'lower':
                    result['bearish_divergence'] = True
                    result['bearish_divergence_points'] = aligned_peaks
                    result['signal'] = 'bearish'
                    result['confidence'] = _calculate_divergence_confidence(aligned_peaks)
        
        # If both divergences detected, prioritize the more recent one
        if result['bullish_divergence'] and result['bearish_divergence']:
            last_bullish = result['bullish_divergence_points'][-1]['price_index'] if result['bullish_divergence_points'] else 0
            last_bearish = result['bearish_divergence_points'][-1]['price_index'] if result['bearish_divergence_points'] else 0
            
            if last_bullish > last_bearish:
                result['bearish_divergence'] = False
                result['bearish_divergence_points'] = []
            else:
                result['bullish_divergence'] = False
                result['bullish_divergence_points'] = []
        
    except Exception as e:
        logger.error(f"Error detecting RSI divergence: {e}")
    
    return result


def detect_macd_divergence(
    close_prices: pd.Series,
    macd_histogram: pd.Series,
    lookback_days: int = 60,
    num_peaks: int = 3,
    min_peak_distance: int = 5
) -> Dict[str, Any]:
    """
    Detect MACD divergences (bullish and bearish).
    
    Args:
        close_prices: Series of closing prices
        macd_histogram: Series of MACD histogram values
        lookback_days: Number of days to look back (default: 60)
        num_peaks: Number of peaks to compare (default: 3)
        min_peak_distance: Minimum distance between peaks (default: 5)
        
    Returns:
        Dict with divergence information
    """
    result = {
        'bullish_divergence': False,
        'bearish_divergence': False,
        'bullish_divergence_points': [],
        'bearish_divergence_points': [],
        'signal': None,
        'confidence': None
    }
    
    if len(close_prices) < lookback_days or len(macd_histogram) < lookback_days:
        return result
    
    try:
        # Use only the lookback period
        recent_prices = close_prices.iloc[-lookback_days:]
        recent_macd = macd_histogram.iloc[-lookback_days:]
        
        # Detect peaks and troughs
        price_extrema = detect_price_peaks_and_troughs(recent_prices, order=min_peak_distance)
        macd_extrema = detect_price_peaks_and_troughs(recent_macd, order=min_peak_distance)
        
        # Check for Bullish Divergence (compare troughs)
        if len(price_extrema['troughs']) >= num_peaks and len(macd_extrema['troughs']) >= num_peaks:
            price_troughs = price_extrema['troughs'][-num_peaks:]
            macd_troughs = macd_extrema['troughs'][-num_peaks:]
            
            aligned_troughs = _align_extrema(price_troughs, macd_troughs, recent_prices.index, recent_macd.index)
            
            if len(aligned_troughs) >= 2:
                price_trend = _calculate_trend(aligned_troughs, 'price')
                macd_trend = _calculate_trend(aligned_troughs, 'indicator')
                
                if price_trend == 'lower' and macd_trend == 'higher':
                    result['bullish_divergence'] = True
                    result['bullish_divergence_points'] = aligned_troughs
                    result['signal'] = 'bullish'
                    result['confidence'] = _calculate_divergence_confidence(aligned_troughs)
        
        # Check for Bearish Divergence (compare peaks)
        if len(price_extrema['peaks']) >= num_peaks and len(macd_extrema['peaks']) >= num_peaks:
            price_peaks = price_extrema['peaks'][-num_peaks:]
            macd_peaks = macd_extrema['peaks'][-num_peaks:]
            
            aligned_peaks = _align_extrema(price_peaks, macd_peaks, recent_prices.index, recent_macd.index)
            
            if len(aligned_peaks) >= 2:
                price_trend = _calculate_trend(aligned_peaks, 'price')
                macd_trend = _calculate_trend(aligned_peaks, 'indicator')
                
                if price_trend == 'higher' and macd_trend == 'lower':
                    result['bearish_divergence'] = True
                    result['bearish_divergence_points'] = aligned_peaks
                    result['signal'] = 'bearish'
                    result['confidence'] = _calculate_divergence_confidence(aligned_peaks)
        
        # Prioritize more recent divergence
        if result['bullish_divergence'] and result['bearish_divergence']:
            last_bullish = result['bullish_divergence_points'][-1]['price_index'] if result['bullish_divergence_points'] else 0
            last_bearish = result['bearish_divergence_points'][-1]['price_index'] if result['bearish_divergence_points'] else 0
            
            if last_bullish > last_bearish:
                result['bearish_divergence'] = False
                result['bearish_divergence_points'] = []
            else:
                result['bullish_divergence'] = False
                result['bullish_divergence_points'] = []
        
    except Exception as e:
        logger.error(f"Error detecting MACD divergence: {e}")
    
    return result


# ============================================================================
# HELPER FUNCTIONS FOR DIVERGENCE DETECTION
# ============================================================================

def _align_extrema(
    price_extrema: List[Tuple[int, float]],
    indicator_extrema: List[Tuple[int, float]],
    price_index: pd.Index,
    indicator_index: pd.Index,
    max_distance: int = 10
) -> List[Dict[str, Any]]:
    """
    Align price extrema with indicator extrema (find matching peaks/troughs).
    
    Returns:
        List of dicts with aligned extrema points
    """
    aligned = []
    
    for price_idx, price_val in price_extrema:
        # Find closest indicator extrema
        closest_indicator = None
        min_distance = float('inf')
        
        for ind_idx, ind_val in indicator_extrema:
            distance = abs(price_idx - ind_idx)
            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                closest_indicator = (ind_idx, ind_val)
        
        if closest_indicator:
            aligned.append({
                'price_index': price_idx,
                'price_value': price_val,
                'indicator_index': closest_indicator[0],
                'indicator_value': closest_indicator[1],
                'rsi': closest_indicator[1]  # For backward compatibility
            })
    
    return aligned


def _calculate_trend(aligned_points: List[Dict[str, Any]], field: str) -> str:
    """
    Calculate trend direction from aligned points.
    
    Args:
        aligned_points: List of aligned extrema
        field: 'price', 'rsi', or 'indicator'
        
    Returns:
        'higher', 'lower', or 'neutral'
    """
    if len(aligned_points) < 2:
        return 'neutral'
    
    # Map field names
    if field == 'rsi' or field == 'indicator':
        value_key = 'indicator_value' if 'indicator_value' in aligned_points[0] else 'rsi'
    else:
        value_key = 'price_value'
    
    values = [point[value_key] for point in aligned_points]
    
    # Check if values are generally increasing or decreasing
    increasing = 0
    decreasing = 0
    
    for i in range(1, len(values)):
        if values[i] > values[i-1]:
            increasing += 1
        elif values[i] < values[i-1]:
            decreasing += 1
    
    if increasing > decreasing:
        return 'higher'
    elif decreasing > increasing:
        return 'lower'
    else:
        return 'neutral'


def _calculate_divergence_confidence(aligned_points: List[Dict[str, Any]]) -> float:
    """
    Calculate confidence score for divergence (0-100).
    
    Higher confidence when:
    - More aligned points
    - Clearer trend divergence
    - Points are well-spaced
    """
    if len(aligned_points) < 2:
        return 0.0
    
    base_confidence = 50.0
    
    # More points = higher confidence
    point_bonus = min((len(aligned_points) - 2) * 15, 30)
    
    # Calculate trend strength
    price_values = [p['price_value'] for p in aligned_points]
    indicator_values = [p.get('indicator_value', p.get('rsi', 0)) for p in aligned_points]
    
    price_range = max(price_values) - min(price_values)
    indicator_range = max(indicator_values) - min(indicator_values)
    
    # Normalize ranges and calculate divergence strength
    if price_range > 0 and indicator_range > 0:
        strength_bonus = 20.0
    else:
        strength_bonus = 0.0
    
    confidence = base_confidence + point_bonus + strength_bonus
    return min(confidence, 100.0)


# ============================================================================
# COMBINED ANALYSIS
# ============================================================================

def analyze_technical_indicators_with_divergence(
    close_prices: pd.Series,
    high_prices: Optional[pd.Series] = None,
    low_prices: Optional[pd.Series] = None,
    lookback_days: int = 60
) -> Dict[str, Any]:
    """
    Comprehensive technical analysis including RSI, MACD, and divergence detection.
    
    Args:
        close_prices: Series of closing prices
        high_prices: Optional series of high prices
        low_prices: Optional series of low prices
        lookback_days: Days to analyze for divergence (default: 60)
        
    Returns:
        Complete technical analysis with divergence signals
    """
    result = {
        'rsi': {},
        'macd': {},
        'divergences': {
            'rsi': {},
            'macd': {}
        },
        'overall_signal': None
    }
    
    try:
        # Calculate RSI
        rsi_data = calculate_rsi(close_prices)
        result['rsi'] = rsi_data
        
        # Calculate MACD
        macd_data = calculate_macd(close_prices)
        result['macd'] = macd_data
        
        # Detect RSI Divergence
        if rsi_data.get('series'):
            rsi_series = pd.Series(rsi_data['series'], index=close_prices.index)
            rsi_divergence = detect_rsi_divergence(close_prices, rsi_series, lookback_days=lookback_days)
            result['divergences']['rsi'] = rsi_divergence
        
        # Detect MACD Divergence
        if macd_data.get('series') and macd_data['series'].get('histogram'):
            macd_histogram = pd.Series(macd_data['series']['histogram'], index=close_prices.index)
            macd_divergence = detect_macd_divergence(close_prices, macd_histogram, lookback_days=lookback_days)
            result['divergences']['macd'] = macd_divergence
        
        # Determine overall signal
        result['overall_signal'] = _determine_overall_signal(result)
        
    except Exception as e:
        logger.error(f"Error in comprehensive technical analysis: {e}")
    
    return result


def _determine_overall_signal(analysis: Dict[str, Any]) -> str:
    """
    Determine overall trading signal from technical analysis.
    
    Returns:
        'strong_buy', 'buy', 'neutral', 'sell', 'strong_sell'
    """
    signals = []
    
    # RSI signal
    rsi_signal = analysis['rsi'].get('signal')
    if rsi_signal == 'oversold':
        signals.append(2)  # Buy
    elif rsi_signal == 'bullish':
        signals.append(1)
    elif rsi_signal == 'bearish':
        signals.append(-1)
    elif rsi_signal == 'overbought':
        signals.append(-2)  # Sell
    
    # MACD signal
    macd_trend = analysis['macd'].get('trend')
    if macd_trend == 'bullish':
        signals.append(1)
    elif macd_trend == 'bearish':
        signals.append(-1)
    
    # RSI Divergence
    rsi_div = analysis['divergences']['rsi']
    if rsi_div.get('bullish_divergence'):
        signals.append(2)  # Strong buy signal
    elif rsi_div.get('bearish_divergence'):
        signals.append(-2)  # Strong sell signal
    
    # MACD Divergence
    macd_div = analysis['divergences']['macd']
    if macd_div.get('bullish_divergence'):
        signals.append(2)
    elif macd_div.get('bearish_divergence'):
        signals.append(-2)
    
    # Calculate average signal
    if not signals:
        return 'neutral'
    
    avg_signal = sum(signals) / len(signals)
    
    if avg_signal >= 1.5:
        return 'strong_buy'
    elif avg_signal >= 0.5:
        return 'buy'
    elif avg_signal <= -1.5:
        return 'strong_sell'
    elif avg_signal <= -0.5:
        return 'sell'
    else:
        return 'neutral'


# ============================================================================
# BOLLINGER BANDS ADVANCED FEATURES
# ============================================================================

def calculate_bollinger_bands(
    close_prices: pd.Series, 
    period: int = 20, 
    num_std: float = 2.0
) -> Dict[str, Any]:
    """
    Calculate Bollinger Bands with advanced features.
    
    Args:
        close_prices: Series of closing prices
        period: Moving average period (default: 20)
        num_std: Number of standard deviations (default: 2.0)
        
    Returns:
        Dict with:
        - upper, middle, lower: Band values
        - percent_b: Bollinger %B indicator
        - bandwidth: Band width as percentage
        - squeeze: Boolean indicating if bands are squeezed
        - band_walking: Direction of band walking ('upper', 'lower', None)
    """
    result = {
        'upper': None,
        'middle': None,
        'lower': None,
        'percent_b': None,
        'bandwidth': None,
        'squeeze': False,
        'band_walking': None,
        'current_percent_b': None,
        'current_bandwidth': None
    }
    
    if close_prices is None or len(close_prices) < period:
        return result
    
    try:
        # Use core_calculate_bollinger_bands for base calculation
        bands_df = core_calculate_bollinger_bands(close_prices, period, num_std)
        if isinstance(bands_df, pd.DataFrame):
            # Extract bands and percent_b
            upper_band = bands_df['upper'] if 'upper' in bands_df else bands_df.iloc[:,0]
            middle_band = bands_df['middle'] if 'middle' in bands_df else bands_df.iloc[:,1]
            lower_band = bands_df['lower'] if 'lower' in bands_df else bands_df.iloc[:,2]
            percent_b = bands_df['percent_b'] if 'percent_b' in bands_df else None
            bandwidth = bands_df['bandwidth'] if 'bandwidth' in bands_df else None
            # Assign to result
            result['upper'] = upper_band.tolist()
            result['middle'] = middle_band.tolist()
            result['lower'] = lower_band.tolist()
            result['percent_b'] = percent_b.tolist() if percent_b is not None else []
            result['bandwidth'] = bandwidth.tolist() if bandwidth is not None else []
            # Current values
            if percent_b is not None and not percent_b.empty:
                result['current_percent_b'] = float(percent_b.iloc[-1])
            if bandwidth is not None and not bandwidth.empty:
                result['current_bandwidth'] = float(bandwidth.iloc[-1])
            # Squeeze Detection
            lookback = min(125, len(bandwidth)) if bandwidth is not None else 0
            if lookback > 0:
                recent_bandwidth = bandwidth.iloc[-lookback:]
                min_bandwidth = recent_bandwidth.min()
                current_bandwidth_val = bandwidth.iloc[-1] if not bandwidth.empty else None
                if current_bandwidth_val and min_bandwidth:
                    squeeze_threshold = min_bandwidth * 1.2
                    result['squeeze'] = current_bandwidth_val <= squeeze_threshold
            # Band Walking Detection
            if percent_b is not None and len(percent_b) >= 3:
                recent_pb = percent_b.iloc[-3:]
                if (recent_pb >= 0.9).sum() >= 3:
                    result['band_walking'] = 'upper'
                elif (recent_pb <= 0.1).sum() >= 3:
                    result['band_walking'] = 'lower'
            # Ensure boolean values are Python bool, not numpy.bool_
            result['squeeze'] = bool(result.get('squeeze', False))
            return result
        else:
            logger.error("core_calculate_bollinger_bands did not return a DataFrame")
            return result
    except Exception as e:
        logger.error(f"Error calculating Bollinger Bands: {e}")
        return result


def get_bollinger_signal(bollinger_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate trading signals from Bollinger Bands analysis.
    
    Args:
        bollinger_data: Output from calculate_bollinger_bands
        
    Returns:
        Dict with signal, reason, and details
    """
    signal_result = {
        'signal': 'neutral',
        'reason': '',
        'details': {}
    }
    
    try:
        current_pb = bollinger_data.get('current_percent_b')
        squeeze = bollinger_data.get('squeeze', False)
        band_walking = bollinger_data.get('band_walking')
        current_bandwidth = bollinger_data.get('current_bandwidth')
        
        if current_pb is None:
            return signal_result
        
        signal_result['details'] = {
            'percent_b': current_pb,
            'squeeze': squeeze,
            'band_walking': band_walking,
            'bandwidth': current_bandwidth
        }
        
        # Squeeze + breakout setup
        if squeeze:
            if current_pb > 1.0:
                signal_result['signal'] = 'buy'
                signal_result['reason'] = 'Bollinger Squeeze breakout above upper band'
            elif current_pb < 0.0:
                signal_result['signal'] = 'sell'
                signal_result['reason'] = 'Bollinger Squeeze breakout below lower band'
            else:
                signal_result['signal'] = 'watch'
                signal_result['reason'] = 'Bollinger Squeeze detected - volatility breakout imminent'
        
        # Band Walking (strong trend)
        elif band_walking == 'upper':
            signal_result['signal'] = 'strong_buy'
            signal_result['reason'] = 'Strong uptrend - Walking the upper Bollinger Band'
        elif band_walking == 'lower':
            signal_result['signal'] = 'strong_sell'
            signal_result['reason'] = 'Strong downtrend - Walking the lower Bollinger Band'
        
        # Overbought/Oversold
        elif current_pb > 1.0:
            signal_result['signal'] = 'overbought'
            signal_result['reason'] = f'Price above upper band (%B: {current_pb:.2f})'
        elif current_pb < 0.0:
            signal_result['signal'] = 'oversold'
            signal_result['reason'] = f'Price below lower band (%B: {current_pb:.2f})'
        
        # Mean reversion zones
        elif current_pb > 0.8:
            signal_result['signal'] = 'caution_sell'
            signal_result['reason'] = 'Approaching upper band - potential reversal'
        elif current_pb < 0.2:
            signal_result['signal'] = 'caution_buy'
            signal_result['reason'] = 'Approaching lower band - potential reversal'
        
        return signal_result
        
    except Exception as e:
        logger.error(f"Error generating Bollinger signal: {e}")
        return signal_result
