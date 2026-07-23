from __future__ import annotations

import os
from dataclasses import dataclass


def _parse_positive_ints(raw: str, *, fallback: tuple[int, ...]) -> tuple[int, ...]:
    values: list[int] = []
    for item in raw.split(","):
        try:
            value = int(item.strip())
        except ValueError:
            continue
        if value > 0 and value not in values:
            values.append(value)
    return tuple(values) or fallback


@dataclass(frozen=True)
class EngineConfig:
    windows: tuple[int, ...]
    eval_horizons: tuple[int, ...]
    min_history: int
    min_train_size: int
    top_k: int
    recent_eval_size: int
    laplace_alpha: float
    recency_half_life: float

    @classmethod
    def from_env(cls) -> "EngineConfig":
        windows = _parse_positive_ints(
            os.environ.get("ENGINE_WINDOWS", "70,150,300,500,700,1000"),
            fallback=(70, 150, 300, 500, 700, 1000),
        )
        horizons = _parse_positive_ints(
            os.environ.get("ENGINE_EVAL_HORIZONS", "14,28,56"),
            fallback=(14, 28, 56),
        )
        min_train_size = max(10, int(os.environ.get("ENGINE_MIN_TRAIN_SIZE", "50")))
        min_history = max(
            min_train_size + min(horizons),
            int(os.environ.get("ENGINE_MIN_HISTORY", "70")),
        )
        top_k = min(10, max(1, int(os.environ.get("ENGINE_TOP_K", "5"))))
        recent_eval_size = max(1, int(os.environ.get("ENGINE_RECENT_EVAL_SIZE", "14")))
        laplace_alpha = max(0.0, float(os.environ.get("ENGINE_LAPLACE_ALPHA", "1")))
        recency_half_life = max(
            1.0,
            float(os.environ.get("ENGINE_RECENCY_HALF_LIFE", "60")),
        )
        return cls(
            windows=windows,
            eval_horizons=horizons,
            min_history=min_history,
            min_train_size=min_train_size,
            top_k=top_k,
            recent_eval_size=recent_eval_size,
            laplace_alpha=laplace_alpha,
            recency_half_life=recency_half_life,
        )
