import math
import os
import random
import re
import time
from typing import Any

import requests

HISTORY_TOKEN_PATTERN = re.compile(r"^\d{4}$")
RETRYABLE_STATUS_CODES = {408, 429, *range(500, 600)}

RETRY_ATTEMPTS = max(1, int(os.environ.get("SCRAPE_RETRY_ATTEMPTS", "3")))
MIN_RESULTS = max(1, int(os.environ.get("SCRAPE_MIN_RESULTS", "28")))
MIN_RETENTION_RATIO = min(
    1.0,
    max(0.0, float(os.environ.get("SCRAPE_MIN_RETENTION_RATIO", "0.5"))),
)
RETRY_JITTER_SECONDS = max(
    0.0,
    float(os.environ.get("SCRAPE_RETRY_JITTER_SECONDS", "1")),
)


def _parse_backoff_seconds() -> list[float]:
    raw = os.environ.get("SCRAPE_RETRY_BACKOFF_SECONDS", "2,5,10")
    values: list[float] = []
    for item in raw.split(","):
        try:
            values.append(max(0.0, float(item.strip())))
        except ValueError:
            continue
    return values or [2.0, 5.0, 10.0]


RETRY_BACKOFF_SECONDS = _parse_backoff_seconds()


def fetch_with_retry(
    url: str,
    *,
    headers: dict[str, str],
    timeout: int | tuple[int, int],
    allow_redirects: bool = True,
    verify: bool = False,
):
    last_error: Exception | None = None

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        status_code: int | None = None
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                allow_redirects=allow_redirects,
                verify=verify,
            )
            status_code = int(getattr(response, "status_code", 200))
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            retryable = status_code is None or status_code in RETRYABLE_STATUS_CODES
            if not retryable or attempt >= RETRY_ATTEMPTS:
                break

            base_delay = RETRY_BACKOFF_SECONDS[min(attempt - 1, len(RETRY_BACKOFF_SECONDS) - 1)]
            delay = base_delay + random.uniform(0, RETRY_JITTER_SECONDS)
            print(
                f"WARN: request_retry url={url} attempt={attempt}/{RETRY_ATTEMPTS} "
                f"delay={delay:.2f}s error={exc}"
            )
            time.sleep(delay)

    raise RuntimeError(
        f"Request gagal setelah {RETRY_ATTEMPTS} percobaan: {url}: {last_error}"
    )


def validate_history_data(data: str) -> tuple[bool, str, list[str]]:
    items = data.split()
    if not items:
        return False, "empty_history", []

    invalid_items = [item for item in items if not HISTORY_TOKEN_PATTERN.fullmatch(item)]
    if invalid_items:
        return False, f"invalid_result:{invalid_items[0]}", items

    if len(items) < MIN_RESULTS:
        return False, f"insufficient_history:{len(items)}<{MIN_RESULTS}", items

    return True, "valid", items


def _response_data(response: Any) -> list[dict[str, Any]]:
    if isinstance(response, dict):
        data = response.get("data")
    else:
        data = getattr(response, "data", None)
    return data if isinstance(data, list) else []


def load_existing_history(supabase, market_id: str) -> str:
    response = (
        supabase.table("markets")
        .select("history_data")
        .eq("id", market_id)
        .limit(1)
        .execute()
    )
    rows = _response_data(response)
    if not rows:
        return ""
    return str(rows[0].get("history_data") or "")


def validate_replacement(new_data: str, existing_data: str) -> tuple[bool, str, list[str]]:
    valid, reason, new_items = validate_history_data(new_data)
    if not valid:
        return False, reason, new_items

    existing_items = existing_data.split()
    if existing_items:
        minimum_safe_count = math.ceil(len(existing_items) * MIN_RETENTION_RATIO)
        if len(new_items) < minimum_safe_count:
            return (
                False,
                f"suspicious_history_drop:{len(new_items)}<{minimum_safe_count} "
                f"previous={len(existing_items)}",
                new_items,
            )

    return True, "safe", new_items


def upsert_market_snapshot(
    supabase,
    *,
    market_id: str,
    name: str,
    history_data: str,
    order: int,
    updated_at: str,
) -> tuple[bool, str, int]:
    existing_data = load_existing_history(supabase, market_id)
    safe, reason, items = validate_replacement(history_data, existing_data)
    if not safe:
        return False, reason, len(items)

    supabase.table("markets").upsert(
        {
            "id": market_id,
            "name": name,
            "history_data": history_data,
            "order": order,
            "updated_at": updated_at,
        }
    ).execute()
    return True, "saved", len(items)
