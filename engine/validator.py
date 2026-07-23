from __future__ import annotations

import re
from typing import Any

from engine.types import MarketHistory

RESULT_PATTERN = re.compile(r"^\d{4}$")


class HistoryValidationError(ValueError):
    pass


def parse_history_data(history_data: str, *, min_history: int) -> tuple[str, ...]:
    results = tuple(str(history_data or "").split())
    if len(results) < min_history:
        raise HistoryValidationError(
            f"insufficient_history:{len(results)}<{min_history}"
        )

    for index, result in enumerate(results):
        if not RESULT_PATTERN.fullmatch(result):
            raise HistoryValidationError(f"invalid_result:index={index}:value={result}")

    return results


def market_history_from_row(row: dict[str, Any], *, min_history: int) -> MarketHistory:
    market_id = str(row.get("id") or "").strip()
    if not market_id:
        raise HistoryValidationError("missing_market_id")

    name = str(row.get("name") or market_id).strip() or market_id
    results = parse_history_data(str(row.get("history_data") or ""), min_history=min_history)

    try:
        order = int(row.get("order") or 0)
    except (TypeError, ValueError) as exc:
        raise HistoryValidationError(f"invalid_order:{row.get('order')}") from exc

    updated_at_raw = row.get("updated_at")
    updated_at = str(updated_at_raw) if updated_at_raw is not None else None

    return MarketHistory(
        market_id=market_id,
        name=name,
        results=results,
        order=order,
        updated_at=updated_at,
    )
