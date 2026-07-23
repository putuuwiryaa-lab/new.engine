from __future__ import annotations

from collections.abc import Sequence

from engine.models.base import normalize_counts
from engine.types import ProbabilityDistribution


class FrequencyModel:
    name = "frequency"

    def __init__(self, *, alpha: float = 1.0):
        self.alpha = max(0.0, float(alpha))

    def predict(self, history: Sequence[str], position: int) -> ProbabilityDistribution:
        if position not in range(4):
            raise ValueError("position must be between 0 and 3")
        counts = [self.alpha] * 10
        for result in history:
            counts[int(result[position])] += 1.0
        return normalize_counts(counts)
