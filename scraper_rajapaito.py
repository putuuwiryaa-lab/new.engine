import re
import requests
from bs4 import BeautifulSoup

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


def scrape_rajapaito_market(url: str, limit: int = 170) -> str:
    try:
        res = requests.get(
            url,
            headers=HEADERS,
            timeout=25,
            allow_redirects=True,
            verify=False,
        )
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
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

            if any(day in row_text for day in ["SENIN", "SELASA", "RABU", "KAMIS", "JUMAT", "SABTU", "MINGGU"]):
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

    except Exception as e:
        print(f"Error scraping Rajapaito {url}: {e}")
        return ""


if __name__ == "__main__":
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    for market_id, url in RAJAPAITO_MARKETS.items():
        data = scrape_rajapaito_market(url)
        items = data.split()
        print(market_id)
        print("TOTAL:", len(items))
        print("LATEST:", items[-1] if items else "KOSONG")
        print(data)
