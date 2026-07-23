from __future__ import annotations

import math
import os
from dataclasses import asdict, dataclass
from typing import Any

from engine.types import EvaluationResult


@dataclass(frozen=True)
class ReleaseGateConfig:
    min_sample_size: int
    min_lift: float
    recent_min_lift: float
    max_miss_streak: int
    min_actual_probability: float
    max_log_loss: float
    max_brier_score: float

    @classmethod
    def from_env(cls) -> "ReleaseGateConfig":
        return cls(
            min_sample_size=max(1, int(os.environ.get("ENGINE_GATE_MIN_SAMPLE_SIZE", "28"))),
            min_lift=float(os.environ.get("ENGINE_GATE_MIN_LIFT", "0.02")),
            recent_min_lift=float(os.environ.get("ENGINE_GATE_RECENT_MIN_LIFT", "0")),
            max_miss_streak=max(0, int(os.environ.get("ENGINE_GATE_MAX_MISS_STREAK", "8"))),
            min_actual_probability=max(
                0.0,
                min(1.0, float(os.environ.get("ENGINE_GATE_MIN_ACTUAL_PROBABILITY", "0.1"))),
            ),
            max_log_loss=max(
                0.0,
                float(os.environ.get("ENGINE_GATE_MAX_LOG_LOSS", str(math.log(10)))),
            ),
            max_brier_score=max(
                0.0,
                float(os.environ.get("ENGINE_GATE_MAX_BRIER_SCORE", "0.9")),
            ),
        )


def config_snapshot(config: ReleaseGateConfig | None = None) -> dict[str, Any]:
    return asdict(config or ReleaseGateConfig.from_env())


def _check(*, passed: bool, actual: float | int, threshold: float | int, operator: str) -> dict:
    return {
        "passed": passed,
        "actual": actual,
        "threshold": threshold,
        "operator": operator,
    }


def evaluate_candidate(
    result: EvaluationResult,
    config: ReleaseGateConfig | None = None,
) -> dict:
    resolved = config or ReleaseGateConfig.from_env()
    recent_threshold = result.baseline_hit_rate + resolved.recent_min_lift

    checks = {
        "sample_size": _check(
            passed=result.sample_size >= resolved.min_sample_size,
            actual=result.sample_size,
            threshold=resolved.min_sample_size,
            operator=">=",
        ),
        "lift": _check(
            passed=result.lift >= resolved.min_lift,
            actual=round(result.lift, 12),
            threshold=resolved.min_lift,
            operator=">=",
        ),
        "recent_hit_rate": _check(
            passed=result.recent_hit_rate >= recent_threshold,
            actual=round(result.recent_hit_rate, 12),
            threshold=round(recent_threshold, 12),
            operator=">=",
        ),
        "longest_miss_streak": _check(
            passed=result.longest_miss_streak <= resolved.max_miss_streak,
            actual=result.longest_miss_streak,
            threshold=resolved.max_miss_streak,
            operator="<=",
        ),
        "mean_actual_probability": _check(
            passed=result.mean_actual_probability >= resolved.min_actual_probability,
            actual=round(result.mean_actual_probability, 12),
            threshold=resolved.min_actual_probability,
            operator=">=",
        ),
        "log_loss": _check(
            passed=result.log_loss <= resolved.max_log_loss,
            actual=round(result.log_loss, 12),
            threshold=round(resolved.max_log_loss, 12),
            operator="<=",
        ),
        "brier_score": _check(
            passed=result.brier_score <= resolved.max_brier_score,
            actual=round(result.brier_score, 12),
            threshold=resolved.max_brier_score,
            operator="<=",
        ),
    }

    reason_map = {
        "sample_size": "insufficient_sample_size",
        "lift": "lift_below_minimum",
        "recent_hit_rate": "recent_hit_rate_below_threshold",
        "longest_miss_streak": "miss_streak_above_maximum",
        "mean_actual_probability": "actual_probability_below_minimum",
        "log_loss": "log_loss_above_maximum",
        "brier_score": "brier_score_above_maximum",
    }
    reasons = [reason_map[name] for name, check in checks.items() if not check["passed"]]

    return {
        "status": "pass" if not reasons else "hold",
        "reasons": reasons,
        "checks": checks,
    }


def summarize_market_gate(position_gates: list[dict]) -> dict:
    passed_positions = sum(gate.get("status") == "pass" for gate in position_gates)
    required_positions = 4
    complete = len(position_gates) == required_positions
    eligible = complete and passed_positions == required_positions

    return {
        "status": "eligible" if eligible else "held",
        "passed_positions": passed_positions,
        "required_positions": required_positions,
        "complete": complete,
        "release_status": "research_only",
    }
