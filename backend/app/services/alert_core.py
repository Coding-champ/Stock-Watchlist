"""
alert_core.py
Centralized alert condition and indicator logic for Stock-Watchlist.
All reusable alert evaluation logic should be placed here.
"""
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Example: Centralized condition evaluation

def evaluate_condition(value: float, condition: str, threshold: float) -> bool:
    if condition == 'gt':
        return value > threshold
    elif condition == 'lt':
        return value < threshold
    elif condition == 'eq':
        return value == threshold
    elif condition == 'gte':
        return value >= threshold
    elif condition == 'lte':
        return value <= threshold
    else:
        logger.warning(f"Unknown condition: {condition}")
        return False

# Example: Centralized indicator-based alert check (to be expanded)
def check_indicator_alert(indicator_data: Dict[str, Any], alert_type: str, options: Dict[str, Any]) -> bool:
    if alert_type == 'ma_cross':
        ma_short = indicator_data.get('ma_short')
        ma_long = indicator_data.get('ma_long')
        condition = options.get('condition')
        threshold = options.get('threshold')
        if ma_short is None or ma_long is None or condition is None or threshold is None:
            return False
        # Example: threshold could be 0 for cross
        cross = (ma_short - ma_long)
        return evaluate_condition(cross, condition, threshold)
    if alert_type == 'percent_from_sma':
        percent = indicator_data.get('percent')
        condition = options.get('condition')
        threshold = options.get('threshold')
        if percent is None or condition is None or threshold is None:
            return False
        return evaluate_condition(percent, condition, threshold)
    if alert_type == 'trailing_stop':
        price = indicator_data.get('price')
        trailing_stop = indicator_data.get('trailing_stop')
        condition = options.get('condition')
        threshold = options.get('threshold')
        if price is None or trailing_stop is None or condition is None or threshold is None:
            return False
        diff = price - trailing_stop
        return evaluate_condition(diff, condition, threshold)
    if alert_type == 'earnings':
        earnings = indicator_data.get('earnings')
        condition = options.get('condition')
        threshold = options.get('threshold')
        if earnings is None or condition is None or threshold is None:
            return False
        return evaluate_condition(earnings, condition, threshold)
    if alert_type == 'composite':
        # Composite: expects indicator_data to contain sub-alert results (bools)
        # Example: all must be True
        return all(indicator_data.values())
    if alert_type == 'volume_spike':
        volume_ratio = indicator_data.get('volume_ratio')
        condition = options.get('condition')
        threshold = options.get('threshold')
        if volume_ratio is None or condition is None or threshold is None:
            return False
        return evaluate_condition(volume_ratio, condition, threshold)
    if alert_type == 'macd_bullish_divergence':
        # MACD bullish divergence is a boolean flag
        return bool(indicator_data.get('divergence', False))
    if alert_type == 'macd_bearish_divergence':
        # MACD bearish divergence is a boolean flag
        return bool(indicator_data.get('divergence', False))
    # Centralized indicator alert logic
    from backend.app.services.alert_core import evaluate_condition
    if alert_type == 'rsi':
        rsi_value = indicator_data.get('rsi')
        condition = options.get('condition')
        threshold = options.get('threshold')
        if rsi_value is None or condition is None or threshold is None:
            return False
        return evaluate_condition(rsi_value, condition, threshold)
    if alert_type == 'volatility':
        volatility = indicator_data.get('volatility')
        condition = options.get('condition')
        threshold = options.get('threshold')
        if volatility is None or condition is None or threshold is None:
            return False
        return evaluate_condition(volatility, condition, threshold)
    # Add more indicator types here (MACD, etc.)
    return False

# Add more reusable alert logic as needed
