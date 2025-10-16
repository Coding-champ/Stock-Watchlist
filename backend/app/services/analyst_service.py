import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional
import yfinance as yf

def get_analyst_ratings_summary(ticker_symbol: str) -> Dict:
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    recommendations = ticker.recommendations
    analyst_price_targets = ticker.analyst_price_targets
    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
    result = {
        'symbol': ticker_symbol,
        'current_price': current_price,
        'analyst_price_targets': analyst_price_targets,
        'recommendations': recommendations,
        'info': info
    }
    return result

def analyze_price_targets(data: Dict) -> Dict:
    current_price = data['current_price']
    targets = data['analyst_price_targets']
    info = data['info']
    target_high = targets.get('high') if targets else info.get('targetHighPrice')
    target_low = targets.get('low') if targets else info.get('targetLowPrice')
    target_mean = targets.get('mean') if targets else info.get('targetMeanPrice')
    target_median = targets.get('median') if targets else info.get('targetMedianPrice')
    target_current = targets.get('current') if targets else info.get('targetMeanPrice')
    num_analysts = info.get('numberOfAnalystOpinions', 0)
    analysis = {
        'target_high': round(target_high, 2) if target_high else None,
        'target_low': round(target_low, 2) if target_low else None,
        'target_mean': round(target_mean, 2) if target_mean else None,
        'target_median': round(target_median, 2) if target_median else None,
        'target_current': round(target_current, 2) if target_current else None,
        'num_analysts': num_analysts,
        'current_price': round(current_price, 2) if current_price else None
    }
    if current_price and target_mean:
        analysis['upside_mean'] = round(((target_mean - current_price) / current_price) * 100, 2)
    else:
        analysis['upside_mean'] = None
    if current_price and target_high:
        analysis['upside_high'] = round(((target_high - current_price) / current_price) * 100, 2)
    else:
        analysis['upside_high'] = None
    if current_price and target_low:
        analysis['upside_low'] = round(((target_low - current_price) / current_price) * 100, 2)
    else:
        analysis['upside_low'] = None
    if target_high and target_low:
        analysis['target_spread'] = round(target_high - target_low, 2)
        analysis['target_spread_pct'] = round(((target_high - target_low) / target_low) * 100, 2)
    else:
        analysis['target_spread'] = None
        analysis['target_spread_pct'] = None
    return analysis

def analyze_recommendations(data: Dict) -> Dict:
    recommendations_df = data['recommendations']
    if recommendations_df is None or recommendations_df.empty:
        return {
            'error': 'Keine Empfehlungsdaten verfügbar',
            'current': None,
            'changes_1m': None,
            'changes_3m': None
        }
    if not isinstance(recommendations_df.index, pd.DatetimeIndex):
        recommendations_df.index = pd.to_datetime(recommendations_df.index)
    recommendations_df = recommendations_df.sort_index(ascending=False)
    now = datetime.now()
    one_month_ago = now - timedelta(days=30)
    three_months_ago = now - timedelta(days=90)
    latest_recs = recommendations_df.iloc[0] if len(recommendations_df) > 0 else None
    recs_1m_ago = recommendations_df[recommendations_df.index <= one_month_ago]
    recs_1m_ago = recs_1m_ago.iloc[0] if len(recs_1m_ago) > 0 else None
    recs_3m_ago = recommendations_df[recommendations_df.index <= three_months_ago]
    recs_3m_ago = recs_3m_ago.iloc[0] if len(recs_3m_ago) > 0 else None
    revisions_1m = len(recommendations_df[recommendations_df.index >= one_month_ago])
    revisions_3m = len(recommendations_df[recommendations_df.index >= three_months_ago])
    latest_date = recommendations_df.index[0].strftime('%Y-%m-%d') if len(recommendations_df) > 0 else None
    result = {
        'current': format_recommendation(latest_recs) if latest_recs is not None else None,
        'revisions_1m': revisions_1m,
        'revisions_3m': revisions_3m,
        'changes_1m': calculate_recommendation_changes(recs_1m_ago, latest_recs) if recs_1m_ago is not None else None,
        'changes_3m': calculate_recommendation_changes(recs_3m_ago, latest_recs) if recs_3m_ago is not None else None,
        'latest_date': latest_date,
        'total_recommendations': len(recommendations_df)
    }
    return result

def format_recommendation(rec_series: pd.Series) -> Dict:
    rec_dict = rec_series.to_dict()
    formatted = {
        'strong_buy': rec_dict.get('strongBuy', 0),
        'buy': rec_dict.get('buy', 0),
        'hold': rec_dict.get('hold', 0),
        'sell': rec_dict.get('sell', 0),
        'strong_sell': rec_dict.get('strongSell', 0)
    }
    total = sum(formatted.values())
    formatted['total'] = total
    if total > 0:
        score = (
            formatted['strong_buy'] * 5 +
            formatted['buy'] * 4 +
            formatted['hold'] * 3 +
            formatted['sell'] * 2 +
            formatted['strong_sell'] * 1
        ) / total
        formatted['consensus_score'] = round(score, 2)
        formatted['consensus_rating'] = get_consensus_rating(score)
    else:
        formatted['consensus_score'] = None
        formatted['consensus_rating'] = None
    return formatted

def get_consensus_rating(score: float) -> str:
    if score >= 4.5:
        return "Strong Buy"
    elif score >= 3.5:
        return "Buy"
    elif score >= 2.5:
        return "Hold"
    elif score >= 1.5:
        return "Sell"
    else:
        return "Strong Sell"

def calculate_recommendation_changes(old_recs: Optional[pd.Series], new_recs: Optional[pd.Series]) -> Optional[Dict]:
    if old_recs is None or new_recs is None:
        return None
    old = format_recommendation(old_recs)
    new = format_recommendation(new_recs)
    changes = {
        'strong_buy': new['strong_buy'] - old['strong_buy'],
        'buy': new['buy'] - old['buy'],
        'hold': new['hold'] - old['hold'],
        'sell': new['sell'] - old['sell'],
        'strong_sell': new['strong_sell'] - old['strong_sell'],
        'score_change': round(new['consensus_score'] - old['consensus_score'], 2) if new['consensus_score'] and old['consensus_score'] else None
    }
    return changes

def get_complete_analyst_overview(ticker_symbol: str) -> Dict:
    data = get_analyst_ratings_summary(ticker_symbol)
    price_analysis = analyze_price_targets(data)
    recommendation_analysis = analyze_recommendations(data)
    overview = {
        'symbol': ticker_symbol,
        'price_targets': price_analysis,
        'recommendations': recommendation_analysis,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return overview
