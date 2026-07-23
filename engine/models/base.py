from __future__ import annotations

from collections.abc import Sequence

from engine.types import ProbabilityDistribution


def normalize_counts(counts: Sequence[float]) -> ProbabilityDistribution:
    if len(counts) != 10:
        raise ValueError("digit model must return ten values")
    total = float(sum(counts))
    if total <= 0:
        return tuple(0.1 for _ in range(10))
    return tuple(float(value) / total for value in counts)
