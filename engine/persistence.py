from __future__ import annotations

import os
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from engine.config import EngineConfig
from engine.release_gate import config_snapshot as gate_config_snapshot

ENGINE_VERSION = "0.2.0"
RELEASE_STATUS = "research_only"
_TRUE_VALUES = {"1", "true", "yes", "on"}


def persistence_enabled() -> bool:
    return os.environ.get("ENGINE_PERSIST_AUDITS", "false").strip().lower() in _TRUE_VALUES


def configured_run_source() -> str:
    value = os.environ.get("ENGINE_RUN_SOURCE", "manual").strip()
    return value or "manual"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_run_id() -> str:
    return str(uuid.uuid4())


def config_snapshot(config: EngineConfig) -> dict[str, Any]:
    snapshot = asdict(config)
    snapshot["windows"] = list(config.windows)
    snapshot["eval_horizons"] = list(config.eval_horizons)
    snapshot["release_gate"] = gate_config_snapshot()
    return snapshot


def create_run_record(
    client,
    *,
    run_id: str,
    config: EngineConfig,
    started_at: str,
) -> None:
    client.table("engine_runs").insert(
        {
            "id": run_id,
            "engine_version": ENGINE_VERSION,
            "release_status": RELEASE_STATUS,
            "status": "running",
            "source": configured_run_source(),
            "started_at": started_at,
            "config": config_snapshot(config),
        }
    ).execute()


def persist_market_audit(client, *, run_id: str, audit: dict[str, Any]) -> None:
    client.table("engine_market_audits").insert(
        {
            "run_id": run_id,
            "market_id": audit["market_id"],
            "market_name": audit["market_name"],
            "generated_at": audit["generated_at"],
            "history_size": audit["history_size"],
            "history_updated_at": audit.get("history_updated_at"),
            "candidate_count": audit["candidate_count"],
            "release_status": audit["release_status"],
            "audit": audit,
        }
    ).execute()


def final_run_status(*, markets_evaluated: int, engine_error_count: int) -> str:
    if markets_evaluated <= 0:
        return "failed"
    if engine_error_count > 0:
        return "partial"
    return "succeeded"


def finalize_run_record(
    client,
    *,
    run_id: str,
    finished_at: str,
    markets_loaded: int,
    markets_evaluated: int,
    validation_errors: list[dict[str, str]],
    engine_errors: list[dict[str, str]],
) -> None:
    client.table("engine_runs").update(
        {
            "status": final_run_status(
                markets_evaluated=markets_evaluated,
                engine_error_count=len(engine_errors),
            ),
            "finished_at": finished_at,
            "markets_loaded": markets_loaded,
            "markets_evaluated": markets_evaluated,
            "validation_error_count": len(validation_errors),
            "engine_error_count": len(engine_errors),
            "validation_errors": validation_errors,
            "engine_errors": engine_errors,
        }
    ).eq("id", run_id).execute()
