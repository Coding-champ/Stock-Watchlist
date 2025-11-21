"""Utility functions for formatting and computing analyst-related metrics.

Provides granular, pure functions so that higher-level services can
assemble analyst metrics without duplicating logic.

Functions:
    compute_upside_potential(mean_target, current_price)
    classify_consensus_strength(high, low, mean)
    score_recommendations(recommendations)
    aggregate_analyst_metrics(price_targets, current_price, recommendations)
"""
from typing import Optional, Dict, Any, List


def compute_upside_potential(mean_target: Optional[float], current_price: Optional[float]) -> Optional[float]:
    """Compute upside potential in percent given mean target and current price."""
    if mean_target and current_price and current_price > 0:
        return ((mean_target - current_price) / current_price) * 100
    return None


def classify_consensus_strength(high: Optional[float], low: Optional[float], mean: Optional[float]) -> Optional[str]:
    """Classify consensus strength based on target range relative to mean.

    Uses simple range ratio thresholds:
        <20%  -> 'strong'
        <40%  -> 'moderate'
        else  -> 'weak'
    """
    if high and low and mean and mean > 0:
        target_range_pct = ((high - low) / mean) * 100
        if target_range_pct < 20:
            return 'strong'
        if target_range_pct < 40:
            return 'moderate'
        return 'weak'
    return None


def score_recommendations(recommendations: Optional[List[Dict[str, Any]]]) -> Dict[str, Optional[float]]:
    """Compute recommendation score and number of analysts.

    Simple heuristic:
        Strong Buy / Buy dominance -> lower score (better)
        Sell dominance -> higher score (worse)
        1.5 = Strong Buy, 2.0 = Buy, 3.0 = Hold, 4.0 = Sell, 4.5 = Strong Sell
    """
    result = {
        'recommendation_score': None,
        'number_of_analysts': None
    }
    if not recommendations:
        return result

    buy_count = sum(1 for r in recommendations if 'buy' in str(r.get('to_grade', '')).lower())
    sell_count = sum(1 for r in recommendations if 'sell' in str(r.get('to_grade', '')).lower())
    result['number_of_analysts'] = len(recommendations)

    if buy_count > sell_count * 2:
        result['recommendation_score'] = 1.5
    elif buy_count > sell_count:
        result['recommendation_score'] = 2.0
    elif sell_count > buy_count * 2:
        result['recommendation_score'] = 4.5
    elif sell_count > buy_count:
        result['recommendation_score'] = 4.0
    else:
        result['recommendation_score'] = 3.0
    return result


def aggregate_analyst_metrics(price_targets: Optional[Dict[str, float]],
                              current_price: Optional[float],
                              recommendations: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Aggregate all analyst metrics in a single dict matching previous service output.

    Returns keys: upside_potential, target_mean, target_high, target_low,
                  consensus_strength, recommendation_score, number_of_analysts
    """
    result: Dict[str, Any] = {
        'upside_potential': None,
        'target_mean': None,
        'target_high': None,
        'target_low': None,
        'consensus_strength': None,
        'recommendation_score': None,
        'number_of_analysts': None
    }

    # Price targets related metrics
    if price_targets:
        mean_target = price_targets.get('mean')
        result['target_mean'] = mean_target
        result['target_high'] = price_targets.get('high')
        result['target_low'] = price_targets.get('low')
        result['upside_potential'] = compute_upside_potential(mean_target, current_price)
        result['consensus_strength'] = classify_consensus_strength(
            price_targets.get('high'), price_targets.get('low'), mean_target
        )

    # Recommendations
    rec_scores = score_recommendations(recommendations)
    result.update(rec_scores)

    return result
