from __future__ import annotations

from engine.config import EngineConfig
from engine.models import FrequencyModel, RecencyWeightedFrequencyModel
from engine.types import ProbabilityModel


def build_model_registry(config: EngineConfig) -> tuple[ProbabilityModel, ...]:
    return (
        FrequencyModel(alpha=config.laplace_alpha),
        RecencyWeightedFrequencyModel(
            alpha=config.laplace_alpha,
            half_life=config.recency_half_life,
        ),
    )
