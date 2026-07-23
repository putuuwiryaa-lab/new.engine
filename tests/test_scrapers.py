import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            response = types.SimpleNamespace(status_code=self.status_code)
            raise requests.HTTPError(f"HTTP {self.status_code}", response=response)


class FakeTableQuery:
    def __init__(self, client, table_name: str):
        self.client = client
        self.table_name = table_name
        self.operation = ""
        self.payload = None
        self.filter_field = None
        self.filter_value = None
        self.limit_value = None

    def select(self, _columns: str):
        self.operation = "select"
        return self

    def eq(self, field: str, value):
        self.filter_field = field
        self.filter_value = value
        return self

    def limit(self, value: int):
        self.limit_value = value
        return self

    def upsert(self, payload: dict):
        self.operation = "upsert"
        self.payload = payload
        return self

    def execute(self):
        if self.table_name != "markets":
            raise AssertionError(f"Unexpected table: {self.table_name}")

        if self.operation == "select":
            rows = list(self.client.rows.values())
            if self.filter_field is not None:
                rows = [
                    row
                    for row in rows
                    if row.get(self.filter_field) == self.filter_value
                ]
            if self.limit_value is not None:
                rows = rows[: self.limit_value]
            return {"data": [dict(row) for row in rows]}

        if self.operation == "upsert":
            if not isinstance(self.payload, dict):
                raise AssertionError("Missing upsert payload")
            self.client.upserts.append(dict(self.payload))
            self.client.rows[self.payload["id"]] = dict(self.payload)
            return {"data": [dict(self.payload)]}

        raise AssertionError(f"Unexpected operation: {self.operation}")


class FakeSupabaseClient:
    def __init__(self):
        self.upserts: list[dict] = []
        self.rows: dict[str, dict] = {}

    def table(self, name: str):
        return FakeTableQuery(self, name)



def load_module(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, ROOT / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ScraperSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["SUPABASE_URL"] = "https://example.supabase.co"
        os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-key"
        os.environ.pop("SUPABASE_ANON_KEY", None)
        os.environ.pop("SCRAPE_HISTORY_LIMIT", None)
        os.environ.pop("RAJAPAITO_ORDER_START", None)
        os.environ.pop("SCRAPE_RETRY_ATTEMPTS", None)
        os.environ.pop("SCRAPE_RETRY_BACKOFF_SECONDS", None)
        os.environ.pop("SCRAPE_RETRY_JITTER_SECONDS", None)
        os.environ.pop("SCRAPE_MIN_RESULTS", None)
        os.environ.pop("SCRAPE_MIN_RETENTION_RATIO", None)

        cls.fake_supabase = FakeSupabaseClient()
        fake_supabase_module = types.ModuleType("supabase")
        fake_supabase_module.create_client = lambda _url, _key: cls.fake_supabase
        sys.modules["supabase"] = fake_supabase_module

        cls.runtime = load_module("scraper_runtime", "scraper_runtime.py")
        sys.modules["scraper_runtime"] = cls.runtime
        cls.legacy = load_module("new_engine_legacy_scraper", "scraper.py")
        cls.rajapaito = load_module(
            "new_engine_rajapaito_scraper", "scraper_rajapaito.py"
        )
        sys.modules["scraper"] = cls.legacy
        sys.modules["scraper_rajapaito"] = cls.rajapaito
        cls.runner = load_module("new_engine_scraper_runner", "run_scrapers.py")

        cls.values = [f"{index:04d}" for index in range(1205)]
        cls.legacy_html = (
            "Tema Terang"
            + "".join(
                "".join(
                    f'<span class="paito-digit">{digit}</span>' for digit in value
                )
                for value in cls.values
            )
            + "RESET"
        )
        cls.rajapaito_html = (
            '<table class="keluaran-table"><tr><th>TAHUN</th></tr>'
            + "".join(f"<tr><td>{value}</td></tr>" for value in cls.values)
            + "</table>"
        )

    def setUp(self):
        self.fake_supabase.upserts.clear()
        self.fake_supabase.rows.clear()

    def test_default_safety_settings(self):
        self.assertEqual(self.legacy.HISTORY_LIMIT, 1200)
        self.assertEqual(self.rajapaito.HISTORY_LIMIT, 1200)
        self.assertEqual(self.runtime.RETRY_ATTEMPTS, 3)
        self.assertEqual(self.runtime.MIN_RESULTS, 28)
        self.assertEqual(self.runtime.MIN_RETENTION_RATIO, 0.5)

    def test_market_registry_sizes(self):
        self.assertEqual(len(self.legacy.MARKETS), 58)
        self.assertEqual(len(self.rajapaito.RAJAPAITO_MARKETS), 13)

    def test_legacy_parser_keeps_latest_1200_results(self):
        with patch.object(
            self.runtime.requests,
            "get",
            return_value=FakeResponse(self.legacy_html),
        ):
            items = self.legacy.scrape_market("/test").split()

        self.assertEqual(len(items), 1200)
        self.assertEqual(items[0], "0005")
        self.assertEqual(items[-1], "1204")

    def test_rajapaito_parser_keeps_latest_1200_results(self):
        with patch.object(
            self.runtime.requests,
            "get",
            return_value=FakeResponse(self.rajapaito_html),
        ):
            items = self.rajapaito.scrape_rajapaito_market(
                "https://example.test"
            ).split()

        self.assertEqual(len(items), 1200)
        self.assertEqual(items[0], "0005")
        self.assertEqual(items[-1], "1204")

    def test_retry_recovers_from_temporary_network_error(self):
        with (
            patch.object(
                self.runtime.requests,
                "get",
                side_effect=[
                    self.runtime.requests.ConnectionError("temporary"),
                    FakeResponse("ok"),
                ],
            ) as mocked_get,
            patch.object(self.runtime.time, "sleep", return_value=None),
            patch.object(self.runtime.random, "uniform", return_value=0),
            patch("builtins.print"),
        ):
            response = self.runtime.fetch_with_retry(
                "https://example.test",
                headers={},
                timeout=(1, 1),
            )

        self.assertEqual(response.text, "ok")
        self.assertEqual(mocked_get.call_count, 2)

    def test_snapshot_guard_rejects_large_history_drop(self):
        existing = " ".join(f"{index:04d}" for index in range(100))
        unsafe = " ".join(f"{index:04d}" for index in range(40))
        safe = " ".join(f"{index:04d}" for index in range(50))

        accepted, reason, _ = self.runtime.validate_replacement(unsafe, existing)
        self.assertFalse(accepted)
        self.assertIn("suspicious_history_drop", reason)

        accepted, reason, _ = self.runtime.validate_replacement(safe, existing)
        self.assertTrue(accepted)
        self.assertEqual(reason, "safe")

    def test_legacy_main_upserts_every_market(self):
        with (
            patch.object(
                self.runtime.requests,
                "get",
                return_value=FakeResponse(self.legacy_html),
            ),
            patch.object(self.legacy.time, "sleep", return_value=None),
            patch("builtins.print"),
        ):
            success, errors = self.legacy.main()

        self.assertEqual((success, errors), (len(self.legacy.MARKETS), 0))
        self.assertEqual(len(self.fake_supabase.upserts), len(self.legacy.MARKETS))
        self.assertTrue(
            all(
                len(row["history_data"].split()) == 1200
                for row in self.fake_supabase.upserts
            )
        )

    def test_rajapaito_main_upserts_every_market(self):
        with (
            patch.object(
                self.runtime.requests,
                "get",
                return_value=FakeResponse(self.rajapaito_html),
            ),
            patch.object(self.rajapaito.time, "sleep", return_value=None),
            patch("builtins.print"),
        ):
            success, errors = self.rajapaito.main()

        self.assertEqual(
            (success, errors),
            (len(self.rajapaito.RAJAPAITO_MARKETS), 0),
        )
        self.assertEqual(
            len(self.fake_supabase.upserts),
            len(self.rajapaito.RAJAPAITO_MARKETS),
        )
        self.assertEqual(self.fake_supabase.upserts[0]["order"], 59)
        self.assertEqual(self.fake_supabase.upserts[-1]["order"], 71)

    def test_runner_returns_success_when_both_jobs_succeed(self):
        with (
            patch.object(self.legacy, "main", return_value=(58, 0)),
            patch.object(self.rajapaito, "main", return_value=(13, 0)),
            patch("builtins.print"),
        ):
            status = self.runner.main()

        self.assertEqual(status, 0)

    def test_runner_returns_failure_when_a_job_has_errors(self):
        with (
            patch.object(self.legacy, "main", return_value=(57, 1)),
            patch.object(self.rajapaito, "main", return_value=(13, 0)),
            patch("builtins.print"),
        ):
            status = self.runner.main()

        self.assertEqual(status, 1)


if __name__ == "__main__":
    unittest.main()
