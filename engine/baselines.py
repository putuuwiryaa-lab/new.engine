from __future__ import annotations

from engine.types import ProbabilityDistribution


def uniform_digit_distribution() -> ProbabilityDistribution:
    return tuple(0.1 for _ in range(10))


def theoretical_top_k_hit_rate(top_k: int) -> float:
    if not 1 <= top_k <= 10:
        raise ValueError("top_k must be between 1 and 10")
    return top_k / 10.0
