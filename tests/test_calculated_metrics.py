"""
Test script for calculated metrics service
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.services import yfinance_service, calculated_metrics_service
import json


def test_calculated_metrics():
    """Test calculated metrics for a sample stock"""
    
    ticker = "AAPL"  # Apple as test example
    print(f"\n{'='*80}")
    print(f"Testing Calculated Metrics for {ticker}")
    print(f"{'='*80}\n")
    
    # Get extended stock data
    print("📊 Fetching extended stock data...")
    extended_data = yfinance_service.get_extended_stock_data(ticker)
    
    if not extended_data:
        print(f"❌ Could not fetch data for {ticker}")
        return
    
    # Flatten data
    stock_data = {}
    for key, value in extended_data.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                stock_data[sub_key] = sub_value
        else:
            stock_data[key] = value
    
    # Get historical prices
    print("📈 Fetching historical price data...")
    historical_prices = yfinance_service.get_historical_prices(ticker, period="1y")
    
    # Get analyst data
    print("👔 Fetching analyst data...")
    try:
        analyst_data = yfinance_service.get_analyst_data(ticker)
        if analyst_data:
            stock_data['price_targets'] = analyst_data.get('price_targets')
            stock_data['recommendations'] = analyst_data.get('recommendations', [])
    except Exception as e:
        print(f"⚠️ Analyst data not available: {e}")
        stock_data['price_targets'] = None
        stock_data['recommendations'] = []
    
    # Calculate all metrics
    print("\n🔬 Calculating all metrics...\n")
    metrics = calculated_metrics_service.calculate_all_metrics(
        stock_data,
        historical_prices
    )
    
    # Display results
    print("\n" + "="*80)
    print("PHASE 1: BASIC INDICATORS")
    print("="*80)
    
    phase1 = metrics['basic_indicators']
    
    print("\n📊 52-Week Metrics:")
    week52 = phase1['week_52_metrics']
    print(f"  Distance from 52W High: {week52['distance_from_52w_high']:.2f}%" if week52['distance_from_52w_high'] else "  N/A")
    print(f"  Distance from 52W Low:  {week52['distance_from_52w_low']:.2f}%" if week52['distance_from_52w_low'] else "  N/A")
    print(f"  Position in 52W Range:  {week52['position_in_52w_range']:.1f}%" if week52['position_in_52w_range'] else "  N/A")
    
    print("\n📈 SMA Metrics:")
    sma = phase1['sma_metrics']
    print(f"  Distance from SMA50:  {sma['distance_from_sma50']:.2f}%" if sma['distance_from_sma50'] else "  N/A")
    print(f"  Distance from SMA200: {sma['distance_from_sma200']:.2f}%" if sma['distance_from_sma200'] else "  N/A")
    print(f"  Golden Cross: {sma['golden_cross']}")
    print(f"  Trend: {sma['trend']}")
    
    print("\n📊 Volume Metrics:")
    vol = phase1['volume_metrics']
    print(f"  Relative Volume: {vol['relative_volume']:.2f}x" if vol['relative_volume'] else "  N/A")
    print(f"  Category: {vol['volume_category']}")
    
    print(f"\n💰 Free Cashflow Yield: {phase1['fcf_yield']:.2f}%" if phase1['fcf_yield'] else "  N/A")
    
    print("\n" + "="*80)
    print("PHASE 2: VALUATION SCORES")
    print("="*80)
    
    phase2 = metrics['valuation_scores']
    
    print(f"\n📉 PEG Ratio: {phase2['peg_ratio']:.2f}" if phase2['peg_ratio'] else "  N/A")
    
    print("\n💎 Value Metrics:")
    value = phase2['value_metrics']
    print(f"  Value Score: {value['value_score']:.1f}/100" if value['value_score'] else "  N/A")
    print(f"  Category: {value['value_category']}")
    print(f"  PE Score: {value['pe_score']:.1f}" if value['pe_score'] else "  N/A")
    print(f"  PB Score: {value['pb_score']:.1f}" if value['pb_score'] else "  N/A")
    print(f"  PS Score: {value['ps_score']:.1f}" if value['ps_score'] else "  N/A")
    
    print("\n⭐ Quality Metrics:")
    quality = phase2['quality_metrics']
    print(f"  Quality Score: {quality['quality_score']:.1f}/100" if quality['quality_score'] else "  N/A")
    print(f"  Category: {quality['quality_category']}")
    print(f"  ROE Score: {quality['roe_score']:.1f}" if quality['roe_score'] else "  N/A")
    print(f"  ROA Score: {quality['roa_score']:.1f}" if quality['roa_score'] else "  N/A")
    
    print("\n💵 Dividend Metrics:")
    div = phase2['dividend_metrics']
    print(f"  Dividend Safety Score: {div['dividend_safety_score']:.1f}/100" if div['dividend_safety_score'] else "  N/A")
    print(f"  Category: {div['safety_category']}")
    
    print("\n" + "="*80)
    print("PHASE 3: ADVANCED ANALYSIS")
    print("="*80)
    
    phase3 = metrics['advanced_analysis']
    
    if phase3.get('macd'):
        print("\n📊 MACD:")
        macd = phase3['macd']
        print(f"  MACD Line: {macd['macd_line']:.2f}" if macd['macd_line'] else "  N/A")
        print(f"  Signal Line: {macd['signal_line']:.2f}" if macd['signal_line'] else "  N/A")
        print(f"  Histogram: {macd['histogram']:.2f}" if macd['histogram'] else "  N/A")
        print(f"  Trend: {macd['trend']}")
    
    if phase3.get('stochastic'):
        print("\n📈 Stochastic Oscillator:")
        stoch = phase3['stochastic']
        print(f"  %K: {stoch['k_percent']:.2f}" if stoch['k_percent'] else "  N/A")
        print(f"  %D: {stoch['d_percent']:.2f}" if stoch['d_percent'] else "  N/A")
        print(f"  Signal: {stoch['signal']}")
        print(f"  Overbought: {stoch['is_overbought']}")
        print(f"  Oversold: {stoch['is_oversold']}")
    
    if phase3.get('volatility'):
        print("\n📉 Volatility Metrics:")
        vol = phase3['volatility']
        print(f"  30-Day: {vol['volatility_30d']:.2f}%" if vol['volatility_30d'] else "  N/A")
        print(f"  90-Day: {vol['volatility_90d']:.2f}%" if vol['volatility_90d'] else "  N/A")
        print(f"  1-Year: {vol['volatility_1y']:.2f}%" if vol['volatility_1y'] else "  N/A")
        print(f"  Category: {vol['volatility_category']}")
    
    if phase3.get('drawdown'):
        print("\n📉 Drawdown Metrics:")
        dd = phase3['drawdown']
        print(f"  Max Drawdown: {dd['max_drawdown']:.2f}%" if dd['max_drawdown'] else "  N/A")
        print(f"  Current Drawdown: {dd['current_drawdown']:.2f}%" if dd['current_drawdown'] else "  N/A")
    
    print("\n👔 Analyst Metrics:")
    analyst = phase3['analyst_metrics']
    print(f"  Upside Potential: {analyst['upside_potential']:.2f}%" if analyst['upside_potential'] else "  N/A")
    print(f"  Target Mean: ${analyst['target_mean']:.2f}" if analyst['target_mean'] else "  N/A")
    print(f"  Consensus: {analyst['consensus_strength']}")
    print(f"  Number of Analysts: {analyst['number_of_analysts']}" if analyst['number_of_analysts'] else "  N/A")
    
    # Beta-Adjusted Metrics
    if phase3.get('beta_adjusted_metrics'):
        print("\n💎 Beta-Adjusted Metrics (Risk-Adjusted Performance):")
        beta_adj = phase3['beta_adjusted_metrics']
        print(f"  Total Return: {beta_adj['total_return']:.2f}%" if beta_adj['total_return'] else "  N/A")
        print(f"  Annualized Return: {beta_adj['annualized_return']:.2f}%" if beta_adj['annualized_return'] else "  N/A")
        print(f"  Sharpe Ratio: {beta_adj['sharpe_ratio']:.3f}" if beta_adj['sharpe_ratio'] else "  N/A")
        print(f"  Alpha: {beta_adj['alpha']:.2f}%" if beta_adj['alpha'] else "  N/A")
        print(f"  Treynor Ratio: {beta_adj['treynor_ratio']:.3f}" if beta_adj['treynor_ratio'] else "  N/A")
        print(f"  Sortino Ratio: {beta_adj['sortino_ratio']:.3f}" if beta_adj['sortino_ratio'] else "  N/A")
        print(f"  Beta-Adjusted Return: {beta_adj['beta_adjusted_return']:.2f}%" if beta_adj['beta_adjusted_return'] else "  N/A")
        print(f"  Information Ratio: {beta_adj['information_ratio']:.3f}" if beta_adj['information_ratio'] else "  N/A")
        print(f"  Downside Deviation: {beta_adj['downside_deviation']:.2f}%" if beta_adj['downside_deviation'] else "  N/A")
        print(f"  Risk Rating: {beta_adj['risk_rating']}")
    
    if phase3.get('risk_adjusted_performance'):
        print("\n⭐ Risk-Adjusted Performance Score:")
        perf = phase3['risk_adjusted_performance']
        print(f"  Overall Score: {perf['overall_score']:.1f}/100" if perf['overall_score'] else "  N/A")
        print(f"  Rating: {perf['rating']}")
        print(f"  Sharpe Contribution: {perf['sharpe_contribution']:.1f}" if perf['sharpe_contribution'] else "  N/A")
        print(f"  Alpha Contribution: {perf['alpha_contribution']:.1f}" if perf['alpha_contribution'] else "  N/A")
        print(f"  Sortino Contribution: {perf['sortino_contribution']:.1f}" if perf['sortino_contribution'] else "  N/A")
        print(f"  Information Contribution: {perf['information_contribution']:.1f}" if perf['information_contribution'] else "  N/A")
    
    print("\n" + "="*80)
    print("✅ All metrics calculated successfully!")
    print("="*80 + "\n")
    
    # Save to file for inspection
    output_file = "calculated_metrics_test_output.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"📁 Full results saved to: {output_file}\n")


if __name__ == "__main__":
    test_calculated_metrics()
