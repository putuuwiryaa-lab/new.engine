from __future__ import annotations

from collections.abc import Sequence

from engine.models.base import normalize_counts
from engine.types import ProbabilityDistribution


class RecencyWeightedFrequencyModel:
    name = "recency_frequency"

    def __init__(self, *, alpha: float = 1.0, half_life: float = 60.0):
        self.alpha = max(0.0, float(alpha))
        self.half_life = max(1.0, float(half_life))

    def predict(self, history: Sequence[str], position: int) -> ProbabilityDistribution:
        if position not in range(4):
            raise ValueError("position must be between 0 and 3")
        counts = [self.alpha] * 10
        for age, result in enumerate(reversed(history)):
            weight = 0.5 ** (age / self.half_life)
            counts[int(result[position])] += weight
        return normalize_counts(counts)
