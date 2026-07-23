from __future__ import annotations

import os
from typing import Any

from engine.types import MarketHistory
from engine.validator import HistoryValidationError, market_history_from_row


def create_supabase_client():
    from supabase import create_client

    url = os.environ["SUPABASE_URL"]
    key = os.environ.get("SUPABASE_ANON_KEY") or os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def _response_data(response: Any) -> list[dict[str, Any]]:
    if isinstance(response, dict):
        data = response.get("data")
    else:
        data = getattr(response, "data", None)
    return data if isinstance(data, list) else []


def load_market_histories(
    client,
    *,
    min_history: int,
    market_ids: set[str] | None = None,
) -> tuple[list[MarketHistory], list[dict[str, str]]]:
    response = (
        client.table("markets")
        .select("id,name,history_data,order,updated_at")
        .order("order")
        .execute()
    )
    rows = _response_data(response)

    histories: list[MarketHistory] = []
    errors: list[dict[str, str]] = []
    for row in rows:
        market_id = str(row.get("id") or "")
        if market_ids and market_id not in market_ids:
            continue
        try:
            histories.append(market_history_from_row(row, min_history=min_history))
        except HistoryValidationError as exc:
            errors.append({"market_id": market_id, "reason": str(exc)})

    return histories, errors
