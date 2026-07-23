import os
import random
import re
import time

from supabase import create_client

from scraper_runtime import fetch_with_retry, upsert_market_snapshot

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY") or os.environ["SUPABASE_SERVICE_ROLE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BASE = "https://159.65.133.131"
HISTORY_LIMIT = int(os.environ.get("SCRAPE_HISTORY_LIMIT", "1200"))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

MARKETS = {
  "MAGNUM CAMBODIA": "/data-pengeluaran-togel-magnum-cambodia/",
  "BULLSEYE": "/data-pengeluaran-togel-bullseye/",
  "SYDNEY LOTTO": "/data-pengeluaran-togel-sdlotto/",
  "SYDNEY POOLS": "/data-pengeluaran-togel-sydney-pools/",
  "CHINA POOLS": "/data-pengeluaran-togel-chinapools/",
  "JAPAN": "/data-pengeluaran-togel-japan/",
  "SINGAPORE": "/data-pengeluaran-togel-singapore/",
  "TAIWAN": "/data-pengeluaran-togel-taiwan/",
  "HONGKONG POOLS": "/data-pengeluaran-togel-hongkong-pools/",
  "HONGKONG LOTTO": "/data-pengeluaran-togel-hklotto/",
  "MARYLAND MIDDAY": "/data-pengeluaran-togel-maryland-midday/",
  "GEORGIA MIDDAY": "/data-pengeluaran-togel-georgia-midday/",
  "MOROCCO 23:59": "/data-pengeluaran-togel-morocco-quatro-23-59-wib/",
  "MICHIGAN MIDDAY": "/data-pengeluaran-togel-michigan-midday/",
  "NEW JERSEY MIDDAY": "/data-pengeluaran-togel-new-jersey-midday/",
  "GERMANY PLUS5": "/data-pengeluaran-togel-germany-plus5/",
  "INDIANA MIDDAY": "/data-pengeluaran-togel-indiana-midday/",
  "TENNESSE MIDDAY": "/data-pengeluaran-togel-tennesse-midday/",
  "KENTUCKY MID": "/data-pengeluaran-togel-kentucky-midday/",
  "TEXAS DAY": "/data-pengeluaran-togel-texas-day/",
  "FLORIDA MID": "/data-pengeluaran-togel-florida-midday/",
  "ILLINOIS MIDDAY": "/data-pengeluaran-togel-illinois-midday/",
  "MISSOURI MIDDAY": "/data-pengeluaran-togel-missouri-midday/",
  "WASHINGTON DC MIDDAY": "/data-pengeluaran-togel-washington-dc-midday/",
  "CONNECTICUT DAY": "/data-pengeluaran-togel-connecticut-day/",
  "VIRGINIA DAY": "/data-pengeluaran-togel-virginia-day/",
  "NEW YORK MID": "/data-pengeluaran-togel-new-york-midday/",
  "MOROCCO 03:00": "/data-pengeluaran-togel-morocco-quatro-03-00-wib/",
  "CAROLINA DAY": "/data-pengeluaran-togel-north-carolina-day/",
  "OREGON 4": "/data-pengeluaran-togel-oregon-04-00-wib/",
  "WEST VIRGINIA": "/data-pengeluaran-togel-west-virginia/",
  "GEORGIA EVE": "/data-pengeluaran-togel-georgia-evening/",
  "OREGON 7": "/data-pengeluaran-togel-oregon-07-00-wib/",
  "TEXAS EVE": "/data-pengeluaran-togel-texas-evening/",
  "TENNESSE EVE": "/data-pengeluaran-togel-tennesse-evening/",
  "MICHIGAN EVE": "/data-pengeluaran-togel-michigan-evening/",
  "MARYLAND EVE": "/data-pengeluaran-togel-maryland-evening/",
  "WASHINGTON DC EVE": "/data-pengeluaran-togel-washington-dc-evening/",
  "CALIFORNIA": "/data-pengeluaran-togel-california/",
  "FLORIDA EVE": "/data-pengeluaran-togel-florida-evening/",
  "MISSOURI EVE": "/data-pengeluaran-togel-missouri-evening/",
  "OREGON 10": "/data-pengeluaran-togel-oregon-10-00-wib/",
  "WISCONSIN EVE": "/data-pengeluaran-togel-wisconsin-evening/",
  "ILLINOIS EVE": "/data-pengeluaran-togel-illinois-evening/",
  "CONNECTICUT NIGHT": "/data-pengeluaran-togel-connecticut-night/",
  "NEW YORK EVE": "/data-pengeluaran-togel-new-york-evening/",
  "INDIANA EVE": "/data-pengeluaran-togel-indiana-evening/",
  "NEW JERSEY EVE": "/data-pengeluaran-togel-new-jersey-evening/",
  "KENTUCKY EVE": "/data-pengeluaran-togel-kentucky-evening/",
  "VIRGINIA NIGHT": "/data-pengeluaran-togel-virginia-night/",
  "TEXAS NIGHT": "/data-pengeluaran-togel-texas-night/",
  "CAROLINA EVE": "/data-pengeluaran-togel-north-carolina-evening/",
  "GEORGIA NIGHT": "/data-pengeluaran-togel-georgia-night/",
  "OREGON 13": "/data-pengeluaran-togel-oregon-13-00-wib/",
  "MOROCCO 18:00": "/data-pengeluaran-togel-morocco-quatro-18-00-wib/",
  "PCSO": "/data-pengeluaran-togel-pcso/",
  "MOROCCO 21:00": "/data-pengeluaran-togel-morocco-quatro-21-00-wib/",
  "TEXAS MORNING": "/data-pengeluaran-togel-texas-morning/",
}

PRIORITY_ORDER = {
  "MAGNUM CAMBODIA": 1,
  "SYDNEY POOLS": 2,
  "SYDNEY LOTTO": 3,
  "CHINA POOLS": 4,
  "JAPAN": 5,
  "SINGAPORE": 6,
  "PCSO": 7,
  "TAIWAN": 8,
  "HONGKONG POOLS": 9,
  "HONGKONG LOTTO": 10,
}


def scrape_market(url):
    try:
        response = fetch_with_retry(
            BASE + url,
            headers=HEADERS,
            timeout=(10, 30),
            verify=False,
        )
        html = response.text

        start_idx = html.find("Tema Terang")
        end_idx = html.find("RESET")

        if start_idx == -1 or end_idx == -1:
            return ""

        section = html[start_idx:end_idx]
        digits = re.findall(r'class="paito-digit">(\d)</span>', section)

        results = []
        for index in range(0, len(digits) - 3, 4):
            results.append(
                digits[index]
                + digits[index + 1]
                + digits[index + 2]
                + digits[index + 3]
            )

        return " ".join(results[-HISTORY_LIMIT:])
    except Exception as exc:
        print(f"ERROR: scrape_failed source=utama url={url} error={exc}")
        return ""


def main():
    next_order = 11
    success = 0
    errors = 0

    for market_id, url in MARKETS.items():
        current_order = PRIORITY_ORDER.get(market_id, next_order)
        if market_id not in PRIORITY_ORDER:
            next_order += 1

        try:
            data = scrape_market(url)
            if not data:
                print(f"REJECT: market={market_id} reason=empty_history")
                errors += 1
                continue

            saved, reason, total = upsert_market_snapshot(
                supabase,
                market_id=market_id,
                name=market_id,
                history_data=data,
                order=current_order,
                updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )

            if saved:
                latest = data.split()[-1]
                print(
                    f"OK: market={market_id} total={total} latest={latest} order={current_order}"
                )
                success += 1
            else:
                print(f"REJECT: market={market_id} total={total} reason={reason}")
                errors += 1
        except Exception as exc:
            print(f"ERROR: market={market_id} error={exc}")
            errors += 1
        finally:
            time.sleep(random.uniform(2, 4))

    print(f"\nSelesai scraper utama: {success} OK, {errors} gagal/reject")
    return success, errors


if __name__ == "__main__":
    _, error_count = main()
    raise SystemExit(1 if error_count else 0)
