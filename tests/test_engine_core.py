from __future__ import annotations

import math
import unittest

from engine.config import EngineConfig
from engine.data_loader import load_market_histories
from engine.evaluator import evaluate_model, rank_digits
from engine.models import FrequencyModel, RecencyWeightedFrequencyModel
from engine.output_builder import build_market_audit
from engine.registry import build_model_registry
from engine.types import MarketHistory
from engine.validator import parse_history_data
from engine.windows import eligible_windows


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def select(self, _columns):
        return self

    def order(self, _column):
        return self

    def execute(self):
        return {"data": self.rows}


class FakeClient:
    def __init__(self, rows):
        self.rows = rows

    def table(self, name):
        if name != "markets":
            raise AssertionError(name)
        return FakeQuery(self.rows)


def config(**overrides) -> EngineConfig:
    values = {
        "windows": (20, 40),
        "eval_horizons": (10,),
        "min_history": 30,
        "min_train_size": 20,
        "top_k": 1,
        "recent_eval_size": 5,
        "laplace_alpha": 1.0,
        "recency_half_life": 5.0,
    }
    values.update(overrides)
    return EngineConfig(**values)


class EngineCoreTests(unittest.TestCase):
    def test_parser_preserves_adjacent_duplicates(self):
        parsed = parse_history_data("1234 1234 5678", min_history=3)
        self.assertEqual(parsed, ("1234", "1234", "5678"))

    def test_adaptive_windows_falls_back_to_available_training(self):
        self.assertEqual(
            eligible_windows(45, (70, 150), min_train_size=20, evaluation_horizon=10),
            (35,),
        )

    def test_frequency_distribution_is_normalized(self):
        model = FrequencyModel(alpha=1.0)
        distribution = model.predict(["1000"] * 9 + ["2000"], 0)
        self.assertTrue(math.isclose(sum(distribution), 1.0))
        self.assertEqual(rank_digits(distribution)[0], 1)

    def test_recency_model_reacts_to_recent_regime(self):
        model = RecencyWeightedFrequencyModel(alpha=0.0, half_life=2.0)
        history = ["1000"] * 20 + ["9000"] * 5
        distribution = model.predict(history, 0)
        self.assertGreater(distribution[9], distribution[1])

    def test_walk_forward_excludes_target_from_training(self):
        class SpyModel:
            name = "spy"

            def __init__(self):
                self.training_sets = []

            def predict(self, history, position):
                self.training_sets.append(tuple(history))
                return tuple(0.1 for _ in range(10))

        results = tuple(f"{index:04d}" for index in range(30))
        model = SpyModel()
        evaluation = evaluate_model(
            model,
            results,
            position=3,
            window=20,
            horizon=5,
            config=config(),
        )
        self.assertEqual(evaluation.sample_size, 5)
        for offset, training in enumerate(model.training_sets):
            target_index = 25 + offset
            self.assertEqual(training[-1], results[target_index - 1])
            self.assertNotEqual(training[-1], results[target_index])

    def test_loader_separates_invalid_markets(self):
        valid_history = " ".join(["1234"] * 30)
        rows = [
            {"id": "VALID", "name": "Valid", "history_data": valid_history, "order": 1},
            {"id": "BAD", "name": "Bad", "history_data": "1234 ABCD", "order": 2},
        ]
        histories, errors = load_market_histories(
            FakeClient(rows),
            min_history=30,
        )
        self.assertEqual([item.market_id for item in histories], ["VALID"])
        self.assertEqual(errors[0]["market_id"], "BAD")

    def test_audit_is_research_only_and_auditable(self):
        cfg = config(top_k=2)
        market = MarketHistory(
            market_id="TEST",
            name="Test",
            results=tuple(["1000"] * 20 + ["2000"] * 20),
            order=1,
        )
        models = build_model_registry(cfg)
        from engine.evaluator import evaluate_market

        evaluations = evaluate_market(market.results, models, cfg)
        audit = build_market_audit(market, evaluations, models, cfg)
        self.assertEqual(audit["release_status"], "research_only")
        self.assertEqual(len(audit["positions"]), 4)
        self.assertGreater(audit["candidate_count"], 0)
        self.assertEqual(len(audit["positions"][0]["top_digits"]), 2)


if __name__ == "__main__":
    unittest.main()
