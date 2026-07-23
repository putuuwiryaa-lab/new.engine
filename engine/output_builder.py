from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from engine.config import EngineConfig
from engine.evaluator import rank_digits, select_best_by_position
from engine.release_gate import (
    ReleaseGateConfig,
    config_snapshot as gate_config_snapshot,
    evaluate_candidate,
    summarize_market_gate,
)
from engine.types import EvaluationResult, MarketHistory, ProbabilityModel


ENGINE_VERSION = "0.2.0"


def build_market_audit(
    market: MarketHistory,
    evaluations: list[EvaluationResult],
    models: tuple[ProbabilityModel, ...],
    config: EngineConfig,
) -> dict:
    model_map = {model.name: model for model in models}
    best = select_best_by_position(evaluations)
    gate_config = ReleaseGateConfig.from_env()
    positions: list[dict] = []
    position_gates: list[dict] = []

    for position in range(4):
        selected = best[position]
        model = model_map[selected.model_name]
        training = market.results[-selected.window :]
        distribution = model.predict(training, position)
        ranking = rank_digits(distribution)
        release_gate = evaluate_candidate(selected, gate_config)
        position_gates.append(release_gate)
        positions.append(
            {
                "position": position,
                "selected_candidate": asdict(selected),
                "ranked_digits": list(ranking),
                "top_digits": list(ranking[: config.top_k]),
                "probabilities": {
                    str(digit): round(distribution[digit], 12) for digit in range(10)
                },
                "release_gate": release_gate,
            }
        )

    return {
        "engine_version": ENGINE_VERSION,
        "release_status": "research_only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "market_id": market.market_id,
        "market_name": market.name,
        "history_size": len(market.results),
        "history_updated_at": market.updated_at,
        "candidate_count": len(evaluations),
        "release_gate_config": gate_config_snapshot(gate_config),
        "market_release_gate": summarize_market_gate(position_gates),
        "positions": positions,
    }
