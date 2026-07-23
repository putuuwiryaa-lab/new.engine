from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

ProbabilityDistribution = tuple[float, ...]


class ProbabilityModel(Protocol):
    name: str

    def predict(self, history: Sequence[str], position: int) -> ProbabilityDistribution:
        ...


@dataclass(frozen=True)
class MarketHistory:
    market_id: str
    name: str
    results: tuple[str, ...]
    order: int
    updated_at: str | None = None


@dataclass(frozen=True)
class EvaluationResult:
    model_name: str
    position: int
    window: int
    horizon: int
    sample_size: int
    top_k: int
    hits: int
    hit_rate: float
    baseline_hit_rate: float
    lift: float
    recent_hit_rate: float
    longest_miss_streak: int
    mean_actual_probability: float
    log_loss: float
    brier_score: float
