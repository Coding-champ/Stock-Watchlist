"""
Alert checking service for monitoring stock alerts
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import yfinance as yf
from backend.app.models import Alert as AlertModel, Stock, StockPriceData, StockFundamentalData
import logging

logger = logging.getLogger(__name__)


class AlertService:
    """Service for checking and triggering stock alerts"""

    def __init__(self, db: Session):
        self.db = db

    def check_all_active_alerts(self) -> Dict[str, Any]:
        """
        Check all active alerts and return triggered ones
        Returns: Dict with triggered alerts and statistics
        """
        alerts = self.db.query(AlertModel).filter(
            AlertModel.is_active == True
        ).all()

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

                # Check the alert condition
                is_triggered = self._check_alert(alert)
                
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

        return {
            'checked_count': checked_count,
            'triggered_count': len(triggered_alerts),
            'error_count': error_count,
            'triggered_alerts': triggered_alerts,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _check_alert(self, alert: AlertModel) -> bool:
        """
        Check if a specific alert condition is met
        Returns: True if alert should be triggered
        """
        alert_type = alert.alert_type
        
        if alert_type == 'price':
            return self._check_price_alert(alert)
        elif alert_type == 'pe_ratio':
            return self._check_pe_ratio_alert(alert)
        elif alert_type == 'rsi':
            return self._check_rsi_alert(alert)
        elif alert_type == 'volatility':
            return self._check_volatility_alert(alert)
        elif alert_type == 'price_change_percent':
            return self._check_price_change_percent_alert(alert)
        elif alert_type == 'ma_cross':
            return self._check_ma_cross_alert(alert)
        elif alert_type == 'volume_spike':
            return self._check_volume_spike_alert(alert)
        elif alert_type == 'earnings':
            return self._check_earnings_alert(alert)
        elif alert_type == 'composite':
            return self._check_composite_alert(alert)
        else:
            logger.warning(f"Unknown alert type: {alert_type}")
            return False

    def _check_price_alert(self, alert: AlertModel) -> bool:
        """Check price alert condition"""
        try:
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            current_price = ticker.info.get('currentPrice') or ticker.info.get('regularMarketPrice')
            
            if current_price is None:
                return False
            
            return self._evaluate_condition(current_price, alert.condition, alert.threshold_value)
        except Exception as e:
            logger.error(f"Error checking price alert: {str(e)}")
            return False

    def _check_pe_ratio_alert(self, alert: AlertModel) -> bool:
        """Check P/E ratio alert condition"""
        try:
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            pe_ratio = ticker.info.get('trailingPE') or ticker.info.get('forwardPE')
            
            if pe_ratio is None:
                return False
            
            return self._evaluate_condition(pe_ratio, alert.condition, alert.threshold_value)
        except Exception as e:
            logger.error(f"Error checking PE ratio alert: {str(e)}")
            return False

    def _check_rsi_alert(self, alert: AlertModel) -> bool:
        """Check RSI alert condition"""
        try:
            # Get historical data for RSI calculation
            ticker = yf.Ticker(alert.stock.ticker_symbol)
            hist = ticker.history(period="1mo")
            
            if len(hist) < 14:
                return False
            
            # Calculate RSI
            rsi = self._calculate_rsi(hist['Close'])
            
            if rsi is None:
                return False
            
            return self._evaluate_condition(rsi, alert.condition, alert.threshold_value)
        except Exception as e:
            logger.error(f"Error checking RSI alert: {str(e)}")
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
            hist = ticker.history(period="3mo")
            
            if len(hist) < 20:
                return False
            
            # Get current volume and average volume
            current_volume = hist['Volume'].iloc[-1]
            avg_volume = hist['Volume'].iloc[-20:-1].mean()  # Exclude today
            
            if avg_volume == 0:
                return False
            
            # Calculate volume spike ratio
            volume_ratio = current_volume / avg_volume
            
            return self._evaluate_condition(volume_ratio, alert.condition, alert.threshold_value)
        except Exception as e:
            logger.error(f"Error checking volume spike alert: {str(e)}")
            return False

    def _calculate_rsi(self, prices, period: int = 14) -> Optional[float]:
        """Calculate RSI (Relative Strength Index)"""
        try:
            deltas = prices.diff()
            gain = deltas.where(deltas > 0, 0)
            loss = -deltas.where(deltas < 0, 0)
            
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1]
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            return None

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
            for condition in alert.composite_conditions:
                alert_type = condition.get('type')
                cond = condition.get('condition')
                value = condition.get('value')
                
                # Create temporary alert-like object
                temp_alert = type('obj', (object,), {
                    'stock': alert.stock,
                    'condition': cond,
                    'threshold_value': value,
                    'timeframe_days': condition.get('timeframe_days')
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
                
                # If any condition fails, return False (AND logic)
                if not result:
                    return False
            
            # All conditions met
            return True
        except Exception as e:
            logger.error(f"Error checking composite alert: {str(e)}")
            return False
