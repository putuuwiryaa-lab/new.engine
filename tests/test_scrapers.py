import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


class FakeQuery:
    def __init__(self, store: list[dict], payload: dict):
        self.store = store
        self.payload = payload

    def execute(self):
        self.store.append(self.payload)
        return {"data": [self.payload]}


class FakeTable:
    def __init__(self, store: list[dict]):
        self.store = store

    def upsert(self, payload: dict):
        return FakeQuery(self.store, payload)


class FakeSupabaseClient:
    def __init__(self):
        self.upserts: list[dict] = []

    def table(self, name: str):
        if name != "markets":
            raise AssertionError(f"Unexpected table: {name}")
        return FakeTable(self.upserts)


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

        cls.fake_supabase = FakeSupabaseClient()
        fake_supabase_module = types.ModuleType("supabase")
        fake_supabase_module.create_client = lambda _url, _key: cls.fake_supabase
        sys.modules["supabase"] = fake_supabase_module

        cls.legacy = load_module("new_engine_legacy_scraper", "scraper.py")
        cls.rajapaito = load_module("new_engine_rajapaito_scraper", "scraper_rajapaito.py")
        sys.modules["scraper"] = cls.legacy
        sys.modules["scraper_rajapaito"] = cls.rajapaito
        cls.runner = load_module("new_engine_scraper_runner", "run_scrapers.py")

        cls.values = [f"{index:04d}" for index in range(1205)]
        cls.legacy_html = (
            "Tema Terang"
            + "".join(
                "".join(f'<span class="paito-digit">{digit}</span>' for digit in value)
                for value in cls.values
            )
            + "RESET"
        )
        cls.rajapaito_html = (
            '<table class="keluaran-table"><tr><th>TAHUN</th></tr>'
            + "".join(f"<tr><td>{value}</td></tr>" for value in cls.values)
            + "</table>"
        )

    def test_default_history_limit_is_1200(self):
        self.assertEqual(self.legacy.HISTORY_LIMIT, 1200)
        self.assertEqual(self.rajapaito.HISTORY_LIMIT, 1200)

    def test_market_registry_sizes(self):
        self.assertEqual(len(self.legacy.MARKETS), 58)
        self.assertEqual(len(self.rajapaito.RAJAPAITO_MARKETS), 13)

    def test_legacy_parser_keeps_latest_1200_results(self):
        with patch.object(
            self.legacy.requests,
            "get",
            return_value=FakeResponse(self.legacy_html),
        ):
            items = self.legacy.scrape_market("/test").split()

        self.assertEqual(len(items), 1200)
        self.assertEqual(items[0], "0005")
        self.assertEqual(items[-1], "1204")

    def test_rajapaito_parser_keeps_latest_1200_results(self):
        with patch.object(
            self.rajapaito.requests,
            "get",
            return_value=FakeResponse(self.rajapaito_html),
        ):
            items = self.rajapaito.scrape_rajapaito_market("https://example.test").split()

        self.assertEqual(len(items), 1200)
        self.assertEqual(items[0], "0005")
        self.assertEqual(items[-1], "1204")

    def test_legacy_main_upserts_every_market(self):
        self.fake_supabase.upserts.clear()

        with (
            patch.object(
                self.legacy.requests,
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
            all(len(row["history_data"].split()) == 1200 for row in self.fake_supabase.upserts)
        )

    def test_rajapaito_main_upserts_every_market(self):
        self.fake_supabase.upserts.clear()

        with (
            patch.object(
                self.rajapaito.requests,
                "get",
                return_value=FakeResponse(self.rajapaito_html),
            ),
            patch("builtins.print"),
        ):
            success, errors = self.rajapaito.main()

        self.assertEqual((success, errors), (len(self.rajapaito.RAJAPAITO_MARKETS), 0))
        self.assertEqual(len(self.fake_supabase.upserts), len(self.rajapaito.RAJAPAITO_MARKETS))
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
