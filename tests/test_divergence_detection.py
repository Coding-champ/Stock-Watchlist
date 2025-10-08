"""
Test script for technical indicators service with divergence detection
"""
import sys
sys.path.append('d:/Programmieren/Projekte/Produktiv/Web Development/Stock-Watchlist')

from backend.app.services.technical_indicators_service import (
    calculate_rsi,
    calculate_macd,
    detect_rsi_divergence,
    detect_macd_divergence,
    analyze_technical_indicators_with_divergence
)
import yfinance as yf
import pandas as pd

def test_technical_indicators():
    """Test RSI, MACD and divergence detection"""
    print("=" * 80)
    print("TESTING TECHNICAL INDICATORS SERVICE")
    print("=" * 80)
    
    # Test with AAPL
    ticker_symbol = "AAPL"
    print(f"\n📊 Testing with {ticker_symbol}...")
    
    try:
        # Get historical data
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="6mo")
        
        if hist.empty:
            print(f"❌ No data available for {ticker_symbol}")
            return
        
        close_prices = hist['Close']
        high_prices = hist['High']
        low_prices = hist['Low']
        
        print(f"✅ Retrieved {len(close_prices)} days of data")
        print(f"   Date range: {hist.index[0].date()} to {hist.index[-1].date()}")
        print(f"   Price range: ${close_prices.min():.2f} - ${close_prices.max():.2f}")
        
        # Test RSI Calculation
        print("\n" + "=" * 80)
        print("1. RSI CALCULATION")
        print("=" * 80)
        rsi_result = calculate_rsi(close_prices)
        
        if rsi_result.get('value'):
            print(f"✅ RSI calculated successfully")
            print(f"   Current RSI: {rsi_result['value']:.2f}")
            print(f"   Signal: {rsi_result['signal']}")
            print(f"   Series length: {len(rsi_result['series']) if rsi_result.get('series') else 0}")
        else:
            print("❌ RSI calculation failed")
        
        # Test MACD Calculation
        print("\n" + "=" * 80)
        print("2. MACD CALCULATION")
        print("=" * 80)
        macd_result = calculate_macd(close_prices)
        
        if macd_result.get('macd_line'):
            print(f"✅ MACD calculated successfully")
            print(f"   MACD Line: {macd_result['macd_line']:.4f}")
            print(f"   Signal Line: {macd_result['signal_line']:.4f}")
            print(f"   Histogram: {macd_result['histogram']:.4f}")
            print(f"   Trend: {macd_result['trend']}")
        else:
            print("❌ MACD calculation failed")
        
        # Test RSI Divergence Detection
        print("\n" + "=" * 80)
        print("3. RSI DIVERGENCE DETECTION")
        print("=" * 80)
        
        if rsi_result.get('series'):
            rsi_series = pd.Series(rsi_result['series'], index=close_prices.index)
            rsi_divergence = detect_rsi_divergence(
                close_prices, 
                rsi_series, 
                lookback_days=60,
                num_peaks=3
            )
            
            print(f"✅ RSI Divergence analysis completed")
            print(f"   Bullish Divergence: {rsi_divergence.get('bullish_divergence', False)}")
            print(f"   Bearish Divergence: {rsi_divergence.get('bearish_divergence', False)}")
            
            if rsi_divergence.get('bullish_divergence'):
                print(f"   🟢 BULLISH SIGNAL DETECTED!")
                print(f"      Confidence: {rsi_divergence.get('confidence', 0):.1f}%")
                print(f"      Points: {len(rsi_divergence.get('bullish_divergence_points', []))}")
            
            if rsi_divergence.get('bearish_divergence'):
                print(f"   🔴 BEARISH SIGNAL DETECTED!")
                print(f"      Confidence: {rsi_divergence.get('confidence', 0):.1f}%")
                print(f"      Points: {len(rsi_divergence.get('bearish_divergence_points', []))}")
            
            if not rsi_divergence.get('bullish_divergence') and not rsi_divergence.get('bearish_divergence'):
                print(f"   ⚪ No divergence detected")
        else:
            print("❌ RSI series not available for divergence detection")
        
        # Test MACD Divergence Detection
        print("\n" + "=" * 80)
        print("4. MACD DIVERGENCE DETECTION")
        print("=" * 80)
        
        if macd_result.get('series') and macd_result['series'].get('histogram'):
            macd_histogram = pd.Series(macd_result['series']['histogram'], index=close_prices.index)
            macd_divergence = detect_macd_divergence(
                close_prices,
                macd_histogram,
                lookback_days=60,
                num_peaks=3
            )
            
            print(f"✅ MACD Divergence analysis completed")
            print(f"   Bullish Divergence: {macd_divergence.get('bullish_divergence', False)}")
            print(f"   Bearish Divergence: {macd_divergence.get('bearish_divergence', False)}")
            
            if macd_divergence.get('bullish_divergence'):
                print(f"   🟢 BULLISH SIGNAL DETECTED!")
                print(f"      Confidence: {macd_divergence.get('confidence', 0):.1f}%")
                print(f"      Points: {len(macd_divergence.get('bullish_divergence_points', []))}")
            
            if macd_divergence.get('bearish_divergence'):
                print(f"   🔴 BEARISH SIGNAL DETECTED!")
                print(f"      Confidence: {macd_divergence.get('confidence', 0):.1f}%")
                print(f"      Points: {len(macd_divergence.get('bearish_divergence_points', []))}")
            
            if not macd_divergence.get('bullish_divergence') and not macd_divergence.get('bearish_divergence'):
                print(f"   ⚪ No divergence detected")
        else:
            print("❌ MACD histogram not available for divergence detection")
        
        # Test Comprehensive Analysis
        print("\n" + "=" * 80)
        print("5. COMPREHENSIVE ANALYSIS")
        print("=" * 80)
        
        analysis = analyze_technical_indicators_with_divergence(
            close_prices=close_prices,
            high_prices=high_prices,
            low_prices=low_prices,
            lookback_days=60
        )
        
        print(f"✅ Comprehensive analysis completed")
        print(f"   Overall Signal: {analysis.get('overall_signal', 'unknown').upper()}")
        print(f"   RSI Value: {analysis['rsi'].get('value', 'N/A')}")
        print(f"   MACD Trend: {analysis['macd'].get('trend', 'N/A')}")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        
        signals = []
        if analysis['divergences']['rsi'].get('bullish_divergence'):
            signals.append("🟢 RSI Bullish Divergence")
        if analysis['divergences']['rsi'].get('bearish_divergence'):
            signals.append("🔴 RSI Bearish Divergence")
        if analysis['divergences']['macd'].get('bullish_divergence'):
            signals.append("🟢 MACD Bullish Divergence")
        if analysis['divergences']['macd'].get('bearish_divergence'):
            signals.append("🔴 MACD Bearish Divergence")
        
        if signals:
            print("Active Divergence Signals:")
            for signal in signals:
                print(f"   {signal}")
        else:
            print("No divergence signals detected")
        
        print(f"\n📈 Trading Recommendation: {analysis.get('overall_signal', 'NEUTRAL').upper()}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_technical_indicators()
