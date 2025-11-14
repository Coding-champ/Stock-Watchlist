"""
Praktische Beispiele für yfinance Datenabfragen
Kategorisiert nach Fundamentaldaten, Technischen Indikatoren und Chartdaten
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_fundamental_data(ticker_symbol: str):
    """Sammelt alle wichtigen Fundamentaldaten"""
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    
    fundamental_data = {
        # Unternehmensdaten
        'company_info': {
            'name': info.get('longName'),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'employees': info.get('fullTimeEmployees'),
            'website': info.get('website'),
            'description': info.get('longBusinessSummary', '')[:200] + '...'
        },
        
        # Finanzielle Kennzahlen
        'financial_ratios': {
            'market_cap': info.get('marketCap'),
            'enterprise_value': info.get('enterpriseValue'),
            'pe_ratio': info.get('trailingPE'),
            'forward_pe': info.get('forwardPE'),
            'peg_ratio': info.get('pegRatio'),
            'price_to_book': info.get('priceToBook'),
            'price_to_sales': info.get('priceToSalesTrailing12Months'),
            'profit_margins': info.get('profitMargins'),
            'operating_margins': info.get('operatingMargins'),
            'return_on_equity': info.get('returnOnEquity'),
            'return_on_assets': info.get('returnOnAssets')
        },
        
        # Dividenden
        'dividend_info': {
            'dividend_rate': info.get('dividendRate'),
            'dividend_yield': info.get('dividendYield'),
            'payout_ratio': info.get('payoutRatio'),
            'five_year_avg_dividend_yield': info.get('fiveYearAvgDividendYield'),
            'ex_dividend_date': info.get('exDividendDate')
        },
        
        # Bilanz
        'balance_sheet_metrics': {
            'total_cash': info.get('totalCash'),
            'total_debt': info.get('totalDebt'),
            'debt_to_equity': info.get('debtToEquity'),
            'current_ratio': info.get('currentRatio'),
            'quick_ratio': info.get('quickRatio'),
            'operating_cashflow': info.get('operatingCashflow'),
            'free_cashflow': info.get('freeCashflow')
        }
    }
    
    return fundamental_data


def get_technical_indicators(ticker_symbol: str):
    """Sammelt technische Indikatoren und Marktdaten"""
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    
    # Historische Daten für technische Analyse
    hist_1y = ticker.history(period="1y")
    hist_3m = ticker.history(period="3mo")
    
    technical_data = {
        # Aktuelle Preisdaten
        'current_prices': {
            'current_price': info.get('currentPrice'),
            'previous_close': info.get('previousClose'),
            'open': info.get('open'),
            'day_low': info.get('dayLow'),
            'day_high': info.get('dayHigh'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh')
        },
        
        # Gleitende Durchschnitte
        'moving_averages': {
            'fifty_day_average': info.get('fiftyDayAverage'),
            'two_hundred_day_average': info.get('twoHundredDayAverage'),
        },
        
        # Volumen-Indikatoren
        'volume_indicators': {
            'volume': info.get('volume'),
            'average_volume': info.get('averageVolume'),
            'average_volume_10days': info.get('averageVolume10days'),
            'relative_volume': info.get('volume', 0) / max(info.get('averageVolume', 1), 1)
        },
        
        # Risiko & Volatilität
        'risk_metrics': {
            'beta': info.get('beta'),
            'shares_outstanding': info.get('sharesOutstanding'),
            'float_shares': info.get('floatShares'),
            'held_percent_insiders': info.get('heldPercentInsiders'),
            'held_percent_institutions': info.get('heldPercentInstitutions')
        },
        
        # Orderbook
        'market_depth': {
            'bid': info.get('bid'),
            'ask': info.get('ask'),
            'bid_size': info.get('bidSize'),
            'ask_size': info.get('askSize')
        }
    }
    
    # Berechne zusätzliche technische Indikatoren aus historischen Daten
    if not hist_1y.empty:
        current_price = hist_1y['Close'].iloc[-1]
        
        # RSI (vereinfacht)
        delta = hist_1y['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        technical_data['calculated_indicators'] = {
            'rsi_14': rsi.iloc[-1] if not rsi.empty else None,
            'price_change_1m': ((current_price - hist_3m['Close'].iloc[0]) / hist_3m['Close'].iloc[0] * 100) if not hist_3m.empty else None,
            'price_change_1y': ((current_price - hist_1y['Close'].iloc[0]) / hist_1y['Close'].iloc[0] * 100),
            'volatility_30d': hist_3m['Close'].pct_change().std() * (252 ** 0.5) if not hist_3m.empty else None
        }
    
    return technical_data


def get_chart_data(ticker_symbol: str):
    """Sammelt Chartdaten für verschiedene Zeiträume"""
    ticker = yf.Ticker(ticker_symbol)
    
    chart_data = {
        # Verschiedene Zeitrahmen
        'historical_data': {
            '1_day': ticker.history(period="1d", interval="1m"),
            '1_week': ticker.history(period="5d", interval="15m"),  
            '1_month': ticker.history(period="1mo", interval="1h"),
            '3_months': ticker.history(period="3mo", interval="1d"),
            '1_year': ticker.history(period="1y", interval="1d"),
            '5_years': ticker.history(period="5y", interval="1wk")
        },
        
        # Corporate Actions
        'corporate_actions': {
            'dividends': ticker.dividends,
            'splits': ticker.splits,
            'actions': ticker.actions
        },
        
        # Erweiterte Daten
        'extended_data': {
            'earnings_dates': ticker.earnings_dates,
            'calendar': ticker.calendar,
            'news': ticker.news[:5] if ticker.news else []  # Letzte 5 News
        }
    }
    
    return chart_data


def get_analyst_data(ticker_symbol: str):
    """Sammelt Analystendaten und Schätzungen"""
    ticker = yf.Ticker(ticker_symbol)
    
    analyst_data = {
        'recommendations': ticker.recommendations,
        'analyst_price_targets': ticker.analyst_price_targets,
        'earnings_estimate': ticker.earnings_estimate,
        'revenue_estimate': ticker.revenue_estimate,
        'eps_trend': ticker.eps_trend,
        'eps_revisions': ticker.eps_revisions,
        'growth_estimates': ticker.growth_estimates
    }
    
    return analyst_data


def get_financial_statements(ticker_symbol: str):
    """Sammelt Finanzdokumente"""
    ticker = yf.Ticker(ticker_symbol)
    
    financial_statements = {
        'income_statement': {
            'annual': ticker.financials,
            'quarterly': ticker.quarterly_financials
        },
        'balance_sheet': {
            'annual': ticker.balance_sheet,
            'quarterly': ticker.quarterly_balance_sheet
        },
        'cash_flow': {
            'annual': ticker.cash_flow,
            'quarterly': ticker.quarterly_cash_flow
        },
        'earnings': ticker.earnings,
        'quarterly_earnings': ticker.quarterly_earnings
    }
    
    return financial_statements


def get_options_data(ticker_symbol: str):
    """Sammelt Optionsdaten"""
    ticker = yf.Ticker(ticker_symbol)
    
    options_data = {
        'expiration_dates': ticker.options,
        'option_chains': {}
    }
    
    # Hole Optionsketten für die nächsten 3 Verfallsdaten
    for exp_date in ticker.options[:3]:
        try:
            options_data['option_chains'][exp_date] = ticker.option_chain(exp_date)
        except:
            continue
    
    return options_data


def comprehensive_stock_analysis(ticker_symbol: str):
    """Komplette Aktienanalyse mit allen verfügbaren Daten"""
    print(f"=== Umfassende Analyse für {ticker_symbol} ===\n")
    
    try:
        # Fundamentaldaten
        print("📊 FUNDAMENTALDATEN")
        fundamental = get_fundamental_data(ticker_symbol)
        print(f"Unternehmen: {fundamental['company_info']['name']}")
        print(f"Sektor: {fundamental['company_info']['sector']}")
        print(f"Marktkapitalisierung: {fundamental['financial_ratios']['market_cap']:,}" if fundamental['financial_ratios']['market_cap'] else "N/A")
        print(f"KGV: {fundamental['financial_ratios']['pe_ratio']}")
        print(f"Dividendenrendite: {fundamental['dividend_info']['dividend_yield']:.2%}" if fundamental['dividend_info']['dividend_yield'] else "Keine Dividende")
        
        # Technische Indikatoren
        print("\n📈 TECHNISCHE INDIKATOREN")
        technical = get_technical_indicators(ticker_symbol)
        print(f"Aktueller Kurs: ${technical['current_prices']['current_price']:.2f}")
        print(f"52-Wochen Spanne: ${technical['current_prices']['fifty_two_week_low']:.2f} - ${technical['current_prices']['fifty_two_week_high']:.2f}")
        print(f"Beta: {technical['risk_metrics']['beta']}")
        print(f"Durchschnittsvolumen: {technical['volume_indicators']['average_volume']:,}")
        
        if 'calculated_indicators' in technical:
            print(f"RSI (14): {technical['calculated_indicators']['rsi_14']:.1f}" if technical['calculated_indicators']['rsi_14'] else "N/A")
            print(f"1-Jahres Performance: {technical['calculated_indicators']['price_change_1y']:.1f}%")
        
        # Chartdaten Info
        print("\n📉 VERFÜGBARE CHARTDATEN")
        chart = get_chart_data(ticker_symbol)
        print(f"Intraday-Daten: {len(chart['historical_data']['1_day'])} Datenpunkte")
        print(f"Langzeitdaten: {len(chart['historical_data']['5_years'])} Wochen")
        print(f"Dividenden: {len(chart['corporate_actions']['dividends'])} Ausschüttungen")
        print(f"Aktuelle News: {len(chart['extended_data']['news'])} Artikel")
        
    except Exception as e:
        print(f"Fehler bei der Analyse: {e}")


if __name__ == "__main__":
    # Beispiel-Analyse
    comprehensive_stock_analysis("AAPL")
    print("\n" + "="*50)
    comprehensive_stock_analysis("MSFT")