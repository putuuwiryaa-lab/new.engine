import os
import random
import re
import time

from bs4 import BeautifulSoup
from supabase import create_client

from scraper_runtime import fetch_with_retry, upsert_market_snapshot

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY") or os.environ["SUPABASE_SERVICE_ROLE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

HISTORY_LIMIT = int(os.environ.get("SCRAPE_HISTORY_LIMIT", "1200"))
RAJAPAITO_ORDER_START = int(os.environ.get("RAJAPAITO_ORDER_START", "59"))

RAJAPAITO_MARKETS = {
    "TENNESSE MORNING": "https://w2.rajapaito1.net/data-togel-tennesse-morning/",
    "MACAU P1": "https://w2.rajapaito1.net/data-togel-macau-p1/",
    "MACAU P2": "https://w2.rajapaito1.net/data-togel-macau-p2/",
    "MACAU P3": "https://w2.rajapaito1.net/data-togel-macau-p3/",
    "MACAU P4": "https://w2.rajapaito1.net/data-togel-macau-p4/",
    "MACAU P5": "https://w2.rajapaito1.net/data-togel-macau-p5/",
    "MACAU P6": "https://w2.rajapaito1.net/data-togel-macau-p6/",
    "PENNSYLVANIA DAY": "https://w2.rajapaito1.net/data-togel-pennsylvania-day/",
    "PENNSYLVANIA EVENING": "https://w2.rajapaito1.net/data-togel-pennsylvania-evening/",
    "DELAWARE DAY": "https://w2.rajapaito1.net/data-togel-delaware-day/",
    "DELAWARE NIGHT": "https://w2.rajapaito1.net/data-togel-delaware-night/",
    "OHIO MIDDAY": "https://w2.rajapaito1.net/data-togel-ohio-midday/",
    "OHIO EVENING": "https://w2.rajapaito1.net/data-togel-ohio-evening/",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def scrape_rajapaito_market(url: str, limit: int = HISTORY_LIMIT) -> str:
    try:
        response = fetch_with_retry(
            url,
            headers=HEADERS,
            timeout=(10, 30),
            allow_redirects=True,
            verify=False,
        )

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.select_one("table.keluaran-table") or soup.find("table")

        if not table:
            return ""

        results = []

        for row in table.find_all("tr"):
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]

            if not cells:
                continue

            row_text = " ".join(cells).upper()

            if "TAHUN" in row_text:
                continue

            if any(
                day in row_text
                for day in ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]
            ):
                continue

            for cell in cells:
                value = cell.strip()
                if re.fullmatch(r"\d{4}", value):
                    results.append(value)

        cleaned = []
        for item in results:
            if not cleaned or cleaned[-1] != item:
                cleaned.append(item)

        return " ".join(cleaned[-limit:])
    except Exception as exc:
        print(f"ERROR: scrape_failed source=rajapaito url={url} error={exc}")
        return ""


def main():
    success = 0
    errors = 0

    for offset, (market_id, url) in enumerate(RAJAPAITO_MARKETS.items()):
        current_order = RAJAPAITO_ORDER_START + offset

        try:
            data = scrape_rajapaito_market(url)
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
            time.sleep(random.uniform(1, 2))

    print(f"\nSelesai scraper Rajapaito: {success} OK, {errors} gagal/reject")
    return success, errors


if __name__ == "__main__":
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _, error_count = main()
    raise SystemExit(1 if error_count else 0)
