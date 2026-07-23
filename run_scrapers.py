import sys
from datetime import datetime, timezone

import urllib3

import scraper
import scraper_rajapaito


def run_job(name, function):
    print(f"\n=== Mulai {name} ===")
    try:
        success, errors = function()
        return success, errors
    except Exception as exc:
        print(f"FATAL: {name} gagal: {exc}")
        return 0, 1


def main():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    started_at = datetime.now(timezone.utc)
    print(f"NEW.ENGINE scraper run dimulai: {started_at.isoformat()}")

    primary_success, primary_errors = run_job("scraper utama", scraper.main)
    rajapaito_success, rajapaito_errors = run_job("scraper Rajapaito", scraper_rajapaito.main)

    success = primary_success + rajapaito_success
    errors = primary_errors + rajapaito_errors
    finished_at = datetime.now(timezone.utc)

    print("\n=== Ringkasan ===")
    print(f"Berhasil: {success}")
    print(f"Gagal/skip: {errors}")
    print(f"Selesai: {finished_at.isoformat()}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
