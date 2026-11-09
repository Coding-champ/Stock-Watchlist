"""Central rule definitions and configuration for the investment check.

``STEP_RULES`` is the single configuration point for criteria and thresholds.
Thresholds intentionally remain ``None`` until the user supplies them. The
orchestrator still returns the collected data, but no step is marked pass/fail
while its configured threshold is missing. Keeping this in code is deliberate
for v1: there is no persistence or settings UI for rules yet.
"""

from typing import Any, Dict, Optional


STEP_RULES: Dict[str, Dict[str, Optional[float]]] = {
    "chart": {"sma": None, "rsi": None, "macd": None, "bollinger": None},
    "fundamentals": {"revenue": None, "profit_margin": None, "roe": None, "debt_to_equity": None},
    "stock_metrics": {"pe_ratio": None, "market_cap": None, "beta": None, "volume": None},
    "peer_market": {"benchmark_outperformance": None, "peer_rank": None},
    "seasonality": {"current_month_return": None},
    "dependent_assets": {"max_correlation": None},
    "allocation": {"max_position_weight": None, "max_sector_weight": None},
}


def get_step_rules() -> Dict[str, Dict[str, Optional[float]]]:
    """Return a copy so callers cannot mutate the central configuration."""
    return {step: criteria.copy() for step, criteria in STEP_RULES.items()}


def evaluate_step(step: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a stable step status while keeping missing rules explicit."""
    criteria = get_step_rules().get(step, {})
    pending = [name for name, threshold in criteria.items() if threshold is None]
    if pending:
        return {
            "status": "not_evaluated",
            "criteria": criteria,
            "pending_thresholds": pending,
            "reason": "Schwellenwerte sind noch nicht konfiguriert.",
        }

    # This branch is deliberately defensive for the later threshold phase.
    # Criteria must be implemented centrally before a pass/fail status is used.
    return {
        "status": "not_evaluated",
        "criteria": criteria,
        "pending_thresholds": [],
        "reason": "Regel ist noch nicht implementiert.",
    }


def evaluate_all(data_by_step: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {
        step: {
            **evaluate_step(step, data),
            "data": data,
            "data_available": bool(data),
        }
        for step, data in data_by_step.items()
    }
