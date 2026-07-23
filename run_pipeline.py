from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Callable

Job = Callable[[], int]


def run_stage(name: str, job: Job) -> int:
    print(f"\n=== Mulai {name} ===")
    try:
        exit_code = int(job())
    except Exception as exc:
        print(f"FATAL: {name} gagal: {exc}")
        return 1

    if exit_code == 0:
        print(f"=== {name} selesai: OK ===")
    else:
        print(f"=== {name} selesai: ERROR exit={exit_code} ===")
    return exit_code


def main(*, scraper_job: Job | None = None, engine_job: Job | None = None) -> int:
    if scraper_job is None:
        from run_scrapers import main as scraper_main

        scraper_job = scraper_main

    if engine_job is None:
        from engine.runner import main as engine_main

        engine_job = engine_main

    started_at = datetime.now(timezone.utc)
    print(f"NEW.ENGINE full pipeline dimulai: {started_at.isoformat()}")

    scraper_exit = run_stage("scraper pipeline", scraper_job)
    engine_exit = run_stage("engine audit seluruh market", engine_job)

    finished_at = datetime.now(timezone.utc)
    final_exit = 1 if scraper_exit or engine_exit else 0

    print("\n=== Ringkasan full pipeline ===")
    print(f"Scraper exit: {scraper_exit}")
    print(f"Engine exit: {engine_exit}")
    print(f"Pipeline exit: {final_exit}")
    print(f"Selesai: {finished_at.isoformat()}")

    return final_exit


if __name__ == "__main__":
    sys.exit(main())
