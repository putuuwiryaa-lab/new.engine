from __future__ import annotations

import json
import os
from typing import Any

from engine.config import EngineConfig
from engine.data_loader import create_supabase_client, load_market_histories
from engine.evaluator import evaluate_market
from engine.output_builder import build_market_audit
from engine.persistence import (
    ENGINE_VERSION,
    RELEASE_STATUS,
    create_run_record,
    finalize_run_record,
    new_run_id,
    persist_market_audit,
    persistence_enabled,
    utc_now_iso,
)
from engine.registry import build_model_registry


def _configured_market_ids() -> set[str] | None:
    raw = os.environ.get("ENGINE_MARKETS", "").strip()
    if not raw:
        return None
    values = {item.strip() for item in raw.split(",") if item.strip()}
    return values or None


def run_engine(*, client=None, config: EngineConfig | None = None) -> dict[str, Any]:
    resolved_config = config or EngineConfig.from_env()
    resolved_client = client or create_supabase_client()
    persist_audits = persistence_enabled()
    run_id = new_run_id()
    started_at = utc_now_iso()

    histories, validation_errors = load_market_histories(
        resolved_client,
        min_history=resolved_config.min_history,
        market_ids=_configured_market_ids(),
    )
    models = build_model_registry(resolved_config)

    if persist_audits:
        create_run_record(
            resolved_client,
            run_id=run_id,
            config=resolved_config,
            started_at=started_at,
        )

    audits: list[dict[str, Any]] = []
    engine_errors: list[dict[str, str]] = []
    for market in histories:
        try:
            evaluations = evaluate_market(market.results, models, resolved_config)
            audit = build_market_audit(market, evaluations, models, resolved_config)
            if persist_audits:
                persist_market_audit(resolved_client, run_id=run_id, audit=audit)
            audits.append(audit)
            print(json.dumps(audit, separators=(",", ":"), sort_keys=True))
        except Exception as exc:
            engine_errors.append({"market_id": market.market_id, "reason": str(exc)})
            print(f"ENGINE_ERROR: market={market.market_id} reason={exc}")

    finished_at = utc_now_iso()
    if persist_audits:
        finalize_run_record(
            resolved_client,
            run_id=run_id,
            finished_at=finished_at,
            markets_loaded=len(histories),
            markets_evaluated=len(audits),
            validation_errors=validation_errors,
            engine_errors=engine_errors,
        )

    summary = {
        "run_id": run_id,
        "engine_version": ENGINE_VERSION,
        "release_status": RELEASE_STATUS,
        "persistence_enabled": persist_audits,
        "started_at": started_at,
        "finished_at": finished_at,
        "markets_loaded": len(histories),
        "markets_evaluated": len(audits),
        "validation_errors": validation_errors,
        "engine_errors": engine_errors,
    }
    print(json.dumps({"engine_summary": summary}, separators=(",", ":"), sort_keys=True))
    return summary


def main() -> int:
    summary = run_engine()
    return 0 if summary["markets_evaluated"] > 0 and not summary["engine_errors"] else 1
