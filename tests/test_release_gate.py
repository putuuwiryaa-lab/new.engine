from __future__ import annotations

import math
import os
import unittest
from unittest.mock import patch

from engine.release_gate import (
    ReleaseGateConfig,
    evaluate_candidate,
    summarize_market_gate,
)
from engine.types import EvaluationResult


def result(**overrides) -> EvaluationResult:
    values = {
        "model_name": "frequency",
        "position": 0,
        "window": 300,
        "horizon": 56,
        "sample_size": 56,
        "top_k": 5,
        "hits": 34,
        "hit_rate": 34 / 56,
        "baseline_hit_rate": 0.5,
        "lift": (34 / 56) - 0.5,
        "recent_hit_rate": 0.64,
        "longest_miss_streak": 4,
        "mean_actual_probability": 0.14,
        "log_loss": 2.0,
        "brier_score": 0.8,
    }
    values.update(overrides)
    return EvaluationResult(**values)


class ReleaseGateTests(unittest.TestCase):
    def test_candidate_passes_all_evidence_checks(self):
        decision = evaluate_candidate(result())

        self.assertEqual(decision["status"], "pass")
        self.assertEqual(decision["reasons"], [])
        self.assertTrue(all(check["passed"] for check in decision["checks"].values()))

    def test_candidate_is_held_with_explicit_reason_codes(self):
        decision = evaluate_candidate(
            result(
                sample_size=14,
                lift=0.0,
                recent_hit_rate=0.4,
                longest_miss_streak=10,
                mean_actual_probability=0.08,
                log_loss=2.5,
                brier_score=0.95,
            )
        )

        self.assertEqual(decision["status"], "hold")
        self.assertEqual(
            set(decision["reasons"]),
            {
                "insufficient_sample_size",
                "lift_below_minimum",
                "recent_hit_rate_below_threshold",
                "miss_streak_above_maximum",
                "actual_probability_below_minimum",
                "log_loss_above_maximum",
                "brier_score_above_maximum",
            },
        )

    def test_market_requires_all_four_positions_to_pass(self):
        passed = {"status": "pass", "reasons": [], "checks": {}}
        held = {"status": "hold", "reasons": ["lift_below_minimum"], "checks": {}}

        self.assertEqual(
            summarize_market_gate([passed, passed, passed, passed])["status"],
            "eligible",
        )
        partial = summarize_market_gate([passed, passed, passed, held])
        self.assertEqual(partial["status"], "held")
        self.assertEqual(partial["passed_positions"], 3)
        self.assertEqual(summarize_market_gate([passed, passed])["status"], "held")

    def test_thresholds_are_configurable_from_environment(self):
        with patch.dict(
            os.environ,
            {
                "ENGINE_GATE_MIN_SAMPLE_SIZE": "56",
                "ENGINE_GATE_MIN_LIFT": "0.05",
                "ENGINE_GATE_RECENT_MIN_LIFT": "0.02",
                "ENGINE_GATE_MAX_MISS_STREAK": "6",
                "ENGINE_GATE_MIN_ACTUAL_PROBABILITY": "0.12",
                "ENGINE_GATE_MAX_LOG_LOSS": str(math.log(8)),
                "ENGINE_GATE_MAX_BRIER_SCORE": "0.82",
            },
            clear=False,
        ):
            config = ReleaseGateConfig.from_env()

        self.assertEqual(config.min_sample_size, 56)
        self.assertEqual(config.min_lift, 0.05)
        self.assertEqual(config.recent_min_lift, 0.02)
        self.assertEqual(config.max_miss_streak, 6)
        self.assertEqual(config.min_actual_probability, 0.12)
        self.assertAlmostEqual(config.max_log_loss, math.log(8))
        self.assertEqual(config.max_brier_score, 0.82)


if __name__ == "__main__":
    unittest.main()
