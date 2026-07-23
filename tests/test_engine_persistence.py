from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from engine.config import EngineConfig
from engine.persistence import (
    create_run_record,
    final_run_status,
    finalize_run_record,
    persist_market_audit,
    persistence_enabled,
)


class FakeMutation:
    def __init__(self, client, table_name: str):
        self.client = client
        self.table_name = table_name
        self.action = ""
        self.payload = None
        self.filters: dict[str, object] = {}

    def insert(self, payload):
        self.action = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.action = "update"
        self.payload = payload
        return self

    def eq(self, column: str, value):
        self.filters[column] = value
        return self

    def execute(self):
        operation = {
            "table": self.table_name,
            "action": self.action,
            "payload": self.payload,
            "filters": self.filters,
        }
        self.client.operations.append(operation)
        return {"data": [self.payload]}


class FakeClient:
    def __init__(self):
        self.operations: list[dict] = []

    def table(self, name: str):
        return FakeMutation(self, name)


def config() -> EngineConfig:
    return EngineConfig(
        windows=(70, 150),
        eval_horizons=(14, 28),
        min_history=70,
        min_train_size=50,
        top_k=5,
        recent_eval_size=14,
        laplace_alpha=1.0,
        recency_half_life=60.0,
    )


class EnginePersistenceTests(unittest.TestCase):
    def test_persistence_is_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(persistence_enabled())

    def test_persistence_accepts_explicit_true_value(self):
        with patch.dict(os.environ, {"ENGINE_PERSIST_AUDITS": "true"}, clear=True):
            self.assertTrue(persistence_enabled())

    def test_run_status_is_deterministic(self):
        self.assertEqual(final_run_status(markets_evaluated=0, engine_error_count=0), "failed")
        self.assertEqual(final_run_status(markets_evaluated=3, engine_error_count=1), "partial")
        self.assertEqual(final_run_status(markets_evaluated=3, engine_error_count=0), "succeeded")

    def test_persistence_writes_run_audit_and_final_state(self):
        client = FakeClient()
        run_id = "00000000-0000-4000-8000-000000000001"
        audit = {
            "engine_version": "0.1.0",
            "release_status": "research_only",
            "generated_at": "2026-07-23T10:00:00+00:00",
            "market_id": "SINGAPORE",
            "market_name": "SINGAPORE",
            "history_size": 1200,
            "history_updated_at": "2026-07-23T08:00:00+00:00",
            "candidate_count": 48,
            "positions": [],
        }

        with patch.dict(os.environ, {"ENGINE_RUN_SOURCE": "test"}, clear=False):
            create_run_record(
                client,
                run_id=run_id,
                config=config(),
                started_at="2026-07-23T09:59:00+00:00",
            )
        persist_market_audit(client, run_id=run_id, audit=audit)
        finalize_run_record(
            client,
            run_id=run_id,
            finished_at="2026-07-23T10:01:00+00:00",
            markets_loaded=1,
            markets_evaluated=1,
            validation_errors=[],
            engine_errors=[],
        )

        self.assertEqual(len(client.operations), 3)
        self.assertEqual(client.operations[0]["table"], "engine_runs")
        self.assertEqual(client.operations[0]["payload"]["status"], "running")
        self.assertEqual(client.operations[0]["payload"]["source"], "test")
        self.assertEqual(client.operations[1]["table"], "engine_market_audits")
        self.assertEqual(client.operations[1]["payload"]["audit"], audit)
        self.assertEqual(client.operations[2]["action"], "update")
        self.assertEqual(client.operations[2]["payload"]["status"], "succeeded")
        self.assertEqual(client.operations[2]["filters"]["id"], run_id)


if __name__ == "__main__":
    unittest.main()
