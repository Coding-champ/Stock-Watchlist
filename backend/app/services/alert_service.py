"""
Alert checking service for monitoring stock alerts
Optimized with batch loading and database-first approach
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
import yfinance as yf
import pandas as pd
from backend.app.models import Alert as AlertModel, Stock, StockPriceData, StockFundamentalData
import logging
from collections import defaultdict

# Import technical indicators
from backend.app.services.technical_indicators_service import (
    calculate_rsi,  # now uses indicators_core.py
    calculate_rsi_series,
    calculate_macd,
    detect_rsi_divergence,
    detect_macd_divergence,
    analyze_technical_indicators_with_divergence
)

# Import optimized yfinance functions
from backend.app.services.yfinance_service import get_fast_stock_data, get_extended_stock_data

logger = logging.getLogger(__name__)


class AlertService:
    """Service for checking and triggering stock alerts with batch optimization"""

    def __init__(self, db: Session):
        self.db = db
        self._stock_data_cache = {}  # Cache for batch-loaded data

    def check_all_active_alerts(self) -> Dict[str, Any]:
        """
        Check all active alerts with batch optimization
        Returns: Dict with triggered alerts and statistics
        """
        alerts = self.db.query(AlertModel).filter(
            AlertModel.is_active == True
        ).all()

        if not alerts:
            return {
                'checked_count': 0,
                'triggered_count': 0,
                'error_count': 0,
                'triggered_alerts': [],
                'timestamp': datetime.utcnow().isoformat()
            }

        # Step 1: Batch load all required stock data
        self._batch_load_stock_data(alerts)

        triggered_alerts = []
        checked_count = 0
        error_count = 0

        for alert in alerts:
            checked_count += 1
            try:
                # Check if alert has expired
                if alert.expiry_date and alert.expiry_date < datetime.utcnow():
                    alert.is_active = False
                    self.db.commit()
                    continue

                # Check the alert condition using cached data
                is_triggered = self._check_alert_optimized(alert)
                
                if is_triggered:
                    # Update alert trigger info
                    alert.last_triggered = datetime.utcnow()
                    alert.trigger_count += 1
                    self.db.commit()
                    
                    triggered_alerts.append({
                        'alert_id': alert.id,
                        'stock_id': alert.stock_id,
                        'stock_name': alert.stock.name,
                        'ticker_symbol': alert.stock.ticker_symbol,
                        'alert_type': alert.alert_type,
                        'condition': alert.condition,
                        'threshold_value': alert.threshold_value,
                        'notes': alert.notes,
                        'triggered_at': alert.last_triggered.isoformat()
                    })
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error checking alert {alert.id}: {str(e)}")

        # Clear cache after processing
        self._stock_data_cache.clear()

        return {
            'checked_count': checked_count,
            'triggered_count': len(triggered_alerts),
            'error_count': error_count,
            'triggered_alerts': triggered_alerts,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _batch_load_stock_data(self, alerts: List[AlertModel]) -> None:
        """
        Batch load stock data for all alerts to minimize API calls
        """
        # Get unique ticker symbols
        ticker_symbols = list(set(alert.stock.ticker_symbol for alert in alerts))
        
        logger.info(f"Batch loading data for {len(ticker_symbols)} unique tickers: {ticker_symbols}")
        
        for ticker_symbol in ticker_symbols:
            try:
                # Load fast data (price, volume) - very fast
                fast_data = get_fast_stock_data(ticker_symbol)
                
                # Load extended data only if needed for specific alert types
                extended_data = None
                needs_extended_data = any(
                    alert.alert_type in ['pe_ratio', 'volatility', 'earnings'] 
                    for alert in alerts 
                    if alert.stock.ticker_symbol == ticker_symbol
                )
                
                if needs_extended_data:
                    extended_data = get_extended_stock_data(ticker_symbol)
                
                # Cache the data
                self._stock_data_cache[ticker_symbol] = {
                    'fast_data': fast_data,
                    'extended_data': extended_data,
                    'loaded_at': datetime.utcnow()
                }
                
            except Exception as e:
                logger.error(f"Error batch loading data for {ticker_symbol}: {str(e)}")
                self._stock_data_cache[ticker_symbol] = None

    def _check_alert_optimized(self, alert: AlertModel) -> bool:
        """
        Check if a specific alert condition is met using cached data
        Returns: True if alert should be triggered
        """
        alert_type = alert.alert_type
        ticker_symbol = alert.stock.ticker_symbol
        
        # Get cached data
        cached_data = self._stock_data_cache.get(ticker_symbol)
        if not cached_data:
            logger.warning(f"No cached data for {ticker_symbol}, skipping alert {alert.id}")
            return False
        
        if alert_type == 'price':
            return self._check_price_alert_optimized(alert, cached_data)
        elif alert_type == 'pe_ratio':
            return self._check_pe_ratio_alert_optimized(alert, cached_data)
        elif alert_type == 'rsi':
            return self._check_rsi_alert_optimized(alert, cached_data)
        elif alert_type == 'rsi_falls_below':
            return self._check_rsi_falls_below_alert_optimized(alert, cached_data)
        elif alert_type == 'rsi_bullish_divergence':
            return self._check_rsi_bullish_divergence_alert_optimized(alert, cached_data)
        elif alert_type == 'rsi_bearish_divergence':
            return self._check_rsi_bearish_divergence_alert_optimized(alert, cached_data)
        elif alert_type == 'macd_bullish_divergence':
            return self._check_macd_bullish_divergence_alert_optimized(alert, cached_data)
        elif alert_type == 'macd_bearish_divergence':
            return self._check_macd_bearish_divergence_alert_optimized(alert, cached_data)
        elif alert_type == 'volatility':
            return self._check_volatility_alert_optimized(alert, cached_data)
        elif alert_type == 'price_change_percent':
            return self._check_price_change_percent_alert_optimized(alert, cached_data)
        elif alert_type == 'ma_cross':
            return self._check_ma_cross_alert_optimized(alert, cached_data)
        elif alert_type == 'volume_spike':
            return self._check_volume_spike_alert_optimized(alert, cached_data)
        elif alert_type == 'percent_from_sma':
            return self._check_percent_from_sma_alert_optimized(alert, cached_data)
        elif alert_type == 'trailing_stop':
            return self._check_trailing_stop_alert_optimized(alert, cached_data)
        elif alert_type == 'earnings':
            return self._check_earnings_alert_optimized(alert, cached_data)
        elif alert_type == 'composite':
            return self._check_composite_alert_optimized(alert, cached_data)
        else:
            logger.warning(f"Unknown alert type: {alert_type}")
            return False

    def _check_price_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check price alert condition using cached data"""
        try:
            fast_data = cached_data.get('fast_data')
            if not fast_data:
                return False
            
            current_price = fast_data['price_data']['current_price']
            if current_price is None:
                return False
            
            return self._evaluate_condition(current_price, alert.condition, alert.threshold_value)
        except Exception as e:
            logger.error(f"Error checking price alert: {str(e)}")
            return False

    def _check_pe_ratio_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check P/E ratio alert condition using cached data"""
        try:
            extended_data = cached_data.get('extended_data')
            if not extended_data:
                return False
            
            pe_ratio = extended_data['financial_ratios']['pe_ratio']
            if pe_ratio is None:
                return False
            
            return self._evaluate_condition(pe_ratio, alert.condition, alert.threshold_value)
        except Exception as e:
            logger.error(f"Error checking PE ratio alert: {str(e)}")
            return False

    def _check_rsi_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check RSI alert using cached data"""
        try:
            # For RSI alerts, we still need historical data
            # This could be further optimized by caching historical data
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            hist = ticker.history(period="1mo")
            
            if len(hist) < 14:  # Need at least 14 days for RSI
                return False
            
            close_prices = hist['Close']
            rsi_result = calculate_rsi(close_prices, period=14)
            
            if rsi_result['value'] is None:
                return False
            
            return self._evaluate_condition(rsi_result['value'], alert.condition, alert.threshold_value)
        except Exception as e:
            logger.error(f"Error checking RSI alert: {str(e)}")
            return False

    def _check_rsi_bullish_divergence_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check for RSI bullish divergence using cached data"""
        try:
            # For divergence detection, we still need historical data
            # This could be further optimized by caching historical data
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            hist = ticker.history(period="3mo")
            
            if len(hist) < 60:
                return False
            
            close_prices = hist['Close']
            
            # Calculate RSI
            rsi_data = calculate_rsi(close_prices)
            if not rsi_data.get('series'):
                return False
            
            rsi_series = pd.Series(rsi_data['series'], index=close_prices.index)
            
            # Detect divergence
            divergence = detect_rsi_divergence(close_prices, rsi_series, lookback_days=60, num_peaks=3)
            
            return divergence.get('bullish_divergence', False)
        except Exception as e:
            logger.error(f"Error checking RSI bullish divergence alert: {str(e)}")
            return False

    def _check_rsi_bearish_divergence_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check for RSI bearish divergence using cached data"""
        try:
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            hist = ticker.history(period="3mo")
            
            if len(hist) < 60:
                return False
            
            close_prices = hist['Close']
            
            # Calculate RSI
            rsi_data = calculate_rsi(close_prices)
            if not rsi_data.get('series'):
                return False
            
            rsi_series = pd.Series(rsi_data['series'], index=close_prices.index)
            
            # Detect divergence
            divergence = detect_rsi_divergence(close_prices, rsi_series, lookback_days=60, num_peaks=3)
            
            return divergence.get('bearish_divergence', False)
        except Exception as e:
            logger.error(f"Error checking RSI bearish divergence alert: {str(e)}")
            return False

    def _check_rsi_falls_below_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check RSI falls below alert using cached data"""
        try:
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            hist = ticker.history(period="1mo")
            
            if len(hist) < 15:  # Need at least 15 days for comparison
                return False
            
            close_prices = hist['Close']
            
            # Calculate RSI for last 2 periods
            rsi_result = calculate_rsi(close_prices.tail(15), period=14)
            
            if rsi_result['value'] is None:
                return False
            
            # Calculate RSI series for comparison
            rsi_series = calculate_rsi(close_prices, period=14)
            
            if not rsi_series.get('series') or len(rsi_series['series']) < 2:
                return False
            
            current_rsi = rsi_series['series'][-1]
            previous_rsi = rsi_series['series'][-2]
            threshold = alert.threshold_value
            
            # Check if RSI fell below threshold from above
            if previous_rsi > threshold and current_rsi <= threshold:
                logger.info(f"RSI fell below {threshold}: Previous={previous_rsi:.2f}, Current={current_rsi:.2f}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking RSI falls below alert: {str(e)}")
            return False

    # Placeholder methods for other alert types (simplified for now)
    def _check_macd_bullish_divergence_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check MACD bullish divergence using cached data"""
        # Simplified implementation - could be further optimized
        return False

    def _check_macd_bearish_divergence_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check MACD bearish divergence using cached data"""
        # Simplified implementation - could be further optimized
        return False

    def _check_volatility_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check volatility alert using cached data"""
        try:
            extended_data = cached_data.get('extended_data')
            if not extended_data:
                return False
            
            volatility = extended_data['risk_metrics']['volatility_30d']
            if volatility is None:
                return False
            
            return self._evaluate_condition(volatility, alert.condition, alert.threshold_value)
        except Exception as e:
            logger.error(f"Error checking volatility alert: {str(e)}")
            return False

    def _check_price_change_percent_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check price change percent alert using cached data"""
        # Simplified implementation - would need historical data
        return False

    def _check_ma_cross_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check moving average cross alert using cached data"""
        # Simplified implementation - would need historical data
        return False

    def _check_volume_spike_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check volume spike alert using cached data"""
        try:
            fast_data = cached_data.get('fast_data')
            if not fast_data:
                return False
            
            current_volume = fast_data['volume_data']['volume']
            avg_volume = fast_data['volume_data']['average_volume']
            
            if current_volume is None or avg_volume is None:
                return False
            
            volume_ratio = current_volume / avg_volume
            return self._evaluate_condition(volume_ratio, alert.condition, alert.threshold_value)
        except Exception as e:
            logger.error(f"Error checking volume spike alert: {str(e)}")
            return False

    def _check_percent_from_sma_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check percent from SMA alert using cached data"""
        # Simplified implementation - would need historical data
        return False

    def _check_trailing_stop_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check trailing stop alert using cached data"""
        # Simplified implementation - would need historical data
        return False

    def _check_earnings_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check earnings alert using cached data"""
        # Simplified implementation - would need earnings data
        return False

    def _check_composite_alert_optimized(self, alert: AlertModel, cached_data: Dict) -> bool:
        """Check composite alert using cached data"""
        # Simplified implementation - would need multiple data points
        return False

    def _check_rsi_bearish_divergence_alert(self, alert: AlertModel) -> bool:
        """Check for RSI bearish divergence"""
        try:
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            hist = ticker.history(period="3mo")
            
            if len(hist) < 60:
                return False
            
            close_prices = hist['Close']
            
            # Calculate RSI
            rsi_data = calculate_rsi(close_prices)
            if not rsi_data.get('series'):
                return False
            
            rsi_series = pd.Series(rsi_data['series'], index=close_prices.index)
            
            # Detect divergence
            divergence = detect_rsi_divergence(close_prices, rsi_series, lookback_days=60, num_peaks=3)
            
            return divergence.get('bearish_divergence', False)
        except Exception as e:
            logger.error(f"Error checking RSI bearish divergence alert: {str(e)}")
            return False

    def _check_macd_bullish_divergence_alert(self, alert: AlertModel) -> bool:
        """Check for MACD bullish divergence"""
        try:
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            hist = ticker.history(period="3mo")
            
            if len(hist) < 60:
                return False
            
            close_prices = hist['Close']
            
            # Calculate MACD
            macd_data = calculate_macd(close_prices)
            if not macd_data.get('series') or not macd_data['series'].get('histogram'):
                return False
            
            macd_histogram = pd.Series(macd_data['series']['histogram'], index=close_prices.index)
            
            # Detect divergence
            divergence = detect_macd_divergence(close_prices, macd_histogram, lookback_days=60, num_peaks=3)
            
            return divergence.get('bullish_divergence', False)
        except Exception as e:
            logger.error(f"Error checking MACD bullish divergence alert: {str(e)}")
            return False

    def _check_macd_bearish_divergence_alert(self, alert: AlertModel) -> bool:
        """Check for MACD bearish divergence"""
        try:
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            hist = ticker.history(period="3mo")
            
            if len(hist) < 60:
                return False
            
            close_prices = hist['Close']
            
            # Calculate MACD
            macd_data = calculate_macd(close_prices)
            if not macd_data.get('series') or not macd_data['series'].get('histogram'):
                return False
            
            macd_histogram = pd.Series(macd_data['series']['histogram'], index=close_prices.index)
            
            # Detect divergence
            divergence = detect_macd_divergence(close_prices, macd_histogram, lookback_days=60, num_peaks=3)
            
            return divergence.get('bearish_divergence', False)
        except Exception as e:
            logger.error(f"Error checking MACD bearish divergence alert: {str(e)}")
            return False

    def _check_rsi_alert(self, alert: AlertModel) -> bool:
        """Check RSI alert condition"""
        try:
            # Get historical data for RSI calculation
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            hist = ticker.history(period="1mo")
            
            if len(hist) < 14:
                return False
            
            # Calculate RSI using canonical implementation
            rsi_result = calculate_rsi(hist['Close'], period=14)
            rsi = rsi_result.get('value') if rsi_result else None
            
            if rsi is None:
                return False
            
            return self._evaluate_condition(rsi, alert.condition, alert.threshold_value)
        except Exception as e:
            logger.error(f"Error checking RSI alert: {str(e)}")
            return False

    def _check_rsi_falls_below_alert(self, alert: AlertModel) -> bool:
        """
        Check if RSI falls below threshold (transition from above to below)
        This is different from the normal RSI alert which checks the current value
        """
        try:
            # Get historical data for RSI calculation
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            hist = ticker.history(period="1mo")
            
            if len(hist) < 15:  # Need at least 15 days (14 for RSI + 1 previous)
                return False
            
            close_prices = hist['Close']
            
            # Use canonical RSI calculation from technical_indicators_service
            rsi_series = calculate_rsi_series(close_prices, period=14)
            
            if rsi_series is None or len(rsi_series) < 2:
                return False
            
            # Get current and previous RSI
            current_rsi = rsi_series.iloc[-1]
            previous_rsi = rsi_series.iloc[-2]
            
            if pd.isna(current_rsi) or pd.isna(previous_rsi):
                return False
            
            # Check if RSI fell below threshold (was above, now below)
            threshold = alert.threshold_value
            if previous_rsi >= threshold and current_rsi < threshold:
                logger.info(f"RSI fell below {threshold}: Previous={previous_rsi:.2f}, Current={current_rsi:.2f}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking RSI falls below alert: {str(e)}")
            return False

    def _check_volatility_alert(self, alert: AlertModel) -> bool:
        """Check volatility alert condition"""
        try:
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            hist = ticker.history(period="1mo")
            
            if len(hist) < 2:
                return False
            
            # Calculate volatility (standard deviation of returns)
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * 100  # Convert to percentage
            
            if volatility is None:
                return False
            
            return self._evaluate_condition(volatility, alert.condition, alert.threshold_value)
        except Exception as e:
            logger.error(f"Error checking volatility alert: {str(e)}")
            return False

    def _check_price_change_percent_alert(self, alert: AlertModel) -> bool:
        """Check percentage price change alert"""
        try:
            timeframe = alert.timeframe_days or 1
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            
            # Get historical data
            hist = ticker.history(period=f"{timeframe + 5}d")
            
            if len(hist) < 2:
                return False
            
            # Calculate percentage change
            current_price = hist['Close'].iloc[-1]
            past_price = hist['Close'].iloc[-timeframe - 1] if len(hist) > timeframe else hist['Close'].iloc[0]
            
            percent_change = ((current_price - past_price) / past_price) * 100
            
            return self._evaluate_condition(percent_change, alert.condition, alert.threshold_value)
        except Exception as e:
            logger.error(f"Error checking price change percent alert: {str(e)}")
            return False

    def _check_ma_cross_alert(self, alert: AlertModel) -> bool:
        """Check moving average crossover alert"""
        try:
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            hist = ticker.history(period="1y")
            
            if len(hist) < 200:
                return False
            
            # Calculate 50-day and 200-day moving averages
            ma_50 = hist['Close'].rolling(window=50).mean()
            ma_200 = hist['Close'].rolling(window=200).mean()
            
            # Check for crossover
            if len(ma_50) < 2 or len(ma_200) < 2:
                return False
            
            current_50 = ma_50.iloc[-1]
            current_200 = ma_200.iloc[-1]
            prev_50 = ma_50.iloc[-2]
            prev_200 = ma_200.iloc[-2]
            
            # Golden Cross: 50-day crosses above 200-day
            if alert.condition == 'cross_above':
                return prev_50 <= prev_200 and current_50 > current_200
            
            # Death Cross: 50-day crosses below 200-day
            elif alert.condition == 'cross_below':
                return prev_50 >= prev_200 and current_50 < current_200
            
            return False
        except Exception as e:
            logger.error(f"Error checking MA cross alert: {str(e)}")
            return False

    def _check_volume_spike_alert(self, alert: AlertModel) -> bool:
        """Check volume spike alert"""
        try:
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            # allow longer period for flexible baseline windows
            hist = ticker.history(period="6mo")

            # Options via composite_conditions (can be dict or list with one dict)
            options = self._get_options(alert)
            baseline_days = int(options.get('baseline_days', 20)) if options else 20
            use_zscore = bool(options.get('use_zscore', False)) if options else False
            exclude_today = bool(options.get('exclude_today', True)) if options else True

            if len(hist) < max(baseline_days + 1, 5):
                return False

            vol_series = hist['Volume']
            current_volume = vol_series.iloc[-1]
            # Define baseline window excluding today by default
            if exclude_today:
                baseline = vol_series.iloc[-baseline_days-1:-1]
            else:
                baseline = vol_series.iloc[-baseline_days:]

            if baseline.empty or baseline.mean() == 0:
                return False

            if use_zscore:
                mean = baseline.mean()
                std = baseline.std(ddof=0)
                if std == 0:
                    return False
                value = (current_volume - mean) / std
            else:
                value = current_volume / baseline.mean()

            return self._evaluate_condition(value, alert.condition, alert.threshold_value)
        except Exception as e:
            logger.error(f"Error checking volume spike alert: {str(e)}")
            return False

    def _check_percent_from_sma_alert(self, alert: AlertModel) -> bool:
        """Check percent distance from SMA (e.g., within/beyond X% of SMA)."""
        try:
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            options = self._get_options(alert)
            sma_period = int(options.get('sma_period', 50)) if options else 50

            # Ensure sufficient history: period + buffer
            needed_days = max(sma_period + 5, 30)
            # Use a period string that covers at least needed_days
            period_str = "1y" if needed_days > 180 else ("6mo" if needed_days > 60 else "3mo")
            hist = ticker.history(period=period_str)

            if len(hist) < sma_period:
                return False

            close = hist['Close']
            sma = close.rolling(window=sma_period).mean()
            current_price = close.iloc[-1]
            current_sma = sma.iloc[-1]

            if pd.isna(current_sma) or current_sma == 0:
                return False

            percent_diff = (current_price - current_sma) / current_sma * 100.0
            return self._evaluate_condition(percent_diff, alert.condition, alert.threshold_value)
        except Exception as e:
            logger.error(f"Error checking percent-from-SMA alert: {str(e)}")
            return False

    def _check_trailing_stop_alert(self, alert: AlertModel) -> bool:
        """
        Check trailing stop based on highest close since a start date.
        Semantics:
          - threshold_value: trailing percent (e.g., 10 for 10%)
          - timeframe_days (optional): if provided, trail from max within last N days;
            otherwise, trail from alert.created_at.
        Trigger when current close <= highest_close * (1 - trailing_percent/100).
        """
        try:
            trail_percent = alert.threshold_value
            if trail_percent is None or trail_percent <= 0:
                return False

            ticker = yf.Ticker(alert.stock.ticker_symbol)

            # Determine start date range
            days = alert.timeframe_days
            if days and days > 0:
                # use a period string to cover the days
                period_str = "max" if days > 3650 else ("5y" if days > 365*3 else ("2y" if days > 365 else f"{days+5}d"))
                hist = ticker.history(period=period_str)
                if len(hist) < 2:
                    return False
                # restrict to last N days
                hist = hist.iloc[-(days+1):]
            else:
                # Since alert creation, fetch enough history
                # Fallback to 5y to be safe, then filter by date
                hist = ticker.history(period="5y")
                if len(hist) < 2:
                    return False
                if alert.created_at:
                    hist = hist[hist.index >= alert.created_at]

            if hist.empty:
                return False

            close = hist['Close']
            current_price = close.iloc[-1]
            highest_close = close.max()
            if pd.isna(highest_close) or highest_close == 0:
                return False

            stop_price = highest_close * (1.0 - (trail_percent / 100.0))
            return current_price <= stop_price
        except Exception as e:
            logger.error(f"Error checking trailing stop alert: {str(e)}")
            return False

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate if a value meets the alert condition"""
        if condition == 'above':
            return value > threshold
        elif condition == 'below':
            return value < threshold
        elif condition == 'equals':
            # Allow small tolerance for floating point comparison
            return abs(value - threshold) < 0.01
        else:
            return False

    def _get_options(self, alert: AlertModel) -> Optional[Dict[str, Any]]:
        """Extract options from composite_conditions which may be a dict or [dict]."""
        opts = alert.composite_conditions
        if isinstance(opts, dict):
            return opts
        if isinstance(opts, list) and opts:
            head = opts[0]
            if isinstance(head, dict):
                return head
        return None

    def check_single_alert(self, alert_id: int) -> Dict[str, Any]:
        """
        Check a single alert manually
        Returns: Dict with alert status and result
        """
        alert = self.db.query(AlertModel).filter(AlertModel.id == alert_id).first()
        
        if not alert:
            return {'error': 'Alert not found'}
        
        try:
            is_triggered = self._check_alert(alert)
            
            if is_triggered:
                alert.last_triggered = datetime.utcnow()
                alert.trigger_count += 1
                self.db.commit()
            
            return {
                'alert_id': alert.id,
                'is_triggered': is_triggered,
                'checked_at': datetime.utcnow().isoformat(),
                'trigger_count': alert.trigger_count
            }
        except Exception as e:
            return {
                'alert_id': alert.id,
                'error': str(e)
            }

    def _check_earnings_alert(self, alert: AlertModel) -> bool:
        """Check earnings date alert"""
        try:
            days_before = alert.timeframe_days or 7  # Default 7 days before
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            
            # Get earnings calendar
            earnings_dates = ticker.earnings_dates
            
            if earnings_dates is None or earnings_dates.empty:
                return False
            
            # Get next earnings date
            future_dates = earnings_dates[earnings_dates.index > datetime.now()]
            if future_dates.empty:
                return False
            
            next_earnings = future_dates.index[0]
            days_until = (next_earnings - datetime.now()).days
            
            # Trigger if within threshold
            if alert.condition == 'before':
                return 0 <= days_until <= days_before
            
            return False
        except Exception as e:
            logger.error(f"Error checking earnings alert: {str(e)}")
            return False

    def _check_composite_alert(self, alert: AlertModel) -> bool:
        """Check composite alert with multiple conditions (AND logic)"""
        try:
            if not alert.composite_conditions:
                return False
            
            # All conditions must be met (AND logic)
            # Normalize to list of dicts
            conditions_list = alert.composite_conditions
            if isinstance(conditions_list, dict):
                conditions_list = [conditions_list]

            for condition in conditions_list:
                alert_type = condition.get('type')
                cond = condition.get('condition')
                value = condition.get('value')

                # Create temporary alert-like object; also pass options via composite_conditions
                temp_alert = type('obj', (object,), {
                    'stock': alert.stock,
                    'condition': cond,
                    'threshold_value': value,
                    'timeframe_days': condition.get('timeframe_days'),
                    'composite_conditions': condition.get('options') or condition  # allow method to read options
                })()
                
                # Check each condition
                result = False
                if alert_type == 'price':
                    result = self._check_price_alert(temp_alert)
                elif alert_type == 'pe_ratio':
                    result = self._check_pe_ratio_alert(temp_alert)
                elif alert_type == 'rsi':
                    result = self._check_rsi_alert(temp_alert)
                elif alert_type == 'volatility':
                    result = self._check_volatility_alert(temp_alert)
                elif alert_type == 'price_change_percent':
                    result = self._check_price_change_percent_alert(temp_alert)
                elif alert_type == 'ma_cross':
                    result = self._check_ma_cross_alert(temp_alert)
                elif alert_type == 'volume_spike':
                    result = self._check_volume_spike_alert(temp_alert)
                elif alert_type == 'percent_from_sma':
                    result = self._check_percent_from_sma_alert(temp_alert)
                elif alert_type == 'trailing_stop':
                    result = self._check_trailing_stop_alert(temp_alert)
                
                # If any condition fails, return False (AND logic)
                if not result:
                    return False
            
            # All conditions met
            return True
        except Exception as e:
            logger.error(f"Error checking composite alert: {str(e)}")
            return False
