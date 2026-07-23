from __future__ import annotations

import unittest

from run_pipeline import main, run_stage


class FullPipelineTests(unittest.TestCase):
    def test_run_stage_returns_zero_for_success(self):
        self.assertEqual(run_stage("ok", lambda: 0), 0)

    def test_run_stage_converts_exception_to_failure(self):
        def fail():
            raise RuntimeError("boom")

        self.assertEqual(run_stage("fail", fail), 1)

    def test_pipeline_runs_engine_after_scraper_failure(self):
        calls: list[str] = []

        def scraper():
            calls.append("scraper")
            return 1

        def engine():
            calls.append("engine")
            return 0

        exit_code = main(scraper_job=scraper, engine_job=engine)

        self.assertEqual(calls, ["scraper", "engine"])
        self.assertEqual(exit_code, 1)

    def test_pipeline_succeeds_only_when_both_stages_succeed(self):
        self.assertEqual(
            main(scraper_job=lambda: 0, engine_job=lambda: 0),
            0,
        )
        self.assertEqual(
            main(scraper_job=lambda: 0, engine_job=lambda: 1),
            1,
        )


if __name__ == "__main__":
    unittest.main()
