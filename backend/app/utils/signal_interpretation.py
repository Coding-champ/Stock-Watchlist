"""
Signal Interpretation Utilities
Provides unified interpretation functions for technical indicators (RSI, MACD, etc.)
Eliminates code duplication across services.
"""


def interpret_rsi(rsi: float) -> str:
    """
    Interpret RSI (Relative Strength Index) value
    
    Args:
        rsi: RSI value (0-100)
        
    Returns:
        Signal string: 'overbought', 'oversold', 'bullish', 'bearish', or 'neutral'
    """
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


def interpret_macd(histogram: float) -> str:
    """
    Interpret MACD histogram value
    
    Args:
        histogram: MACD histogram value
        
    Returns:
        Signal string: 'bullish', 'bearish', or 'neutral'
    """
    if histogram > 0:
        return 'bullish'
    elif histogram < 0:
        return 'bearish'
    else:
        return 'neutral'
