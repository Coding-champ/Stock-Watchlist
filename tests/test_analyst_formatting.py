import math
from backend.app.utils.analyst_formatting import (
    compute_upside_potential,
    classify_consensus_strength,
    score_recommendations,
    aggregate_analyst_metrics,
)


def test_compute_upside_potential():
    assert math.isclose(compute_upside_potential(150, 100), 50.0)
    assert compute_upside_potential(None, 100) is None
    assert compute_upside_potential(150, None) is None


def test_classify_consensus_strength():
    # strong (<20%)
    assert classify_consensus_strength(160, 140, 150) == 'strong'
    # moderate (<40%)
    assert classify_consensus_strength(170, 140, 150) == 'moderate'
    # weak (>=40%)
    assert classify_consensus_strength(200, 100, 150) == 'weak'
    # insufficient data
    assert classify_consensus_strength(None, 100, 150) is None


def test_score_recommendations():
    recs = [
        {'to_grade': 'Strong Buy'},
        {'to_grade': 'Buy'},
        {'to_grade': 'Sell'},
        {'to_grade': 'Hold'},
    ]
    scored = score_recommendations(recs)
    assert scored['number_of_analysts'] == 4
    assert scored['recommendation_score'] == 2.0  # Buy dominance

    strong_buy = [{'to_grade': 'Strong Buy'}, {'to_grade': 'Buy'}, {'to_grade': 'Buy'}]
    scored2 = score_recommendations(strong_buy)
    assert scored2['recommendation_score'] == 1.5

    sell_dom = [{'to_grade': 'Sell'}, {'to_grade': 'Strong Sell'}, {'to_grade': 'Sell'}, {'to_grade': 'Buy'}]
    scored3 = score_recommendations(sell_dom)
    assert scored3['recommendation_score'] == 4.0 or scored3['recommendation_score'] == 4.5


def test_aggregate_analyst_metrics_structure():
    price_targets = {'mean': 150, 'high': 170, 'low': 140}
    recs = [{'to_grade': 'Buy'}, {'to_grade': 'Sell'}, {'to_grade': 'Hold'}]
    agg = aggregate_analyst_metrics(price_targets, 100, recs)
    expected_keys = {
        'upside_potential', 'target_mean', 'target_high', 'target_low',
        'consensus_strength', 'recommendation_score', 'number_of_analysts'
    }
    assert expected_keys.issubset(agg.keys())
    assert agg['upside_potential'] is not None
    assert agg['target_mean'] == 150
    assert agg['consensus_strength'] in {'strong', 'moderate', 'weak'}
    assert agg['number_of_analysts'] == 3
