from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from engine.baselines import theoretical_top_k_hit_rate
from engine.config import EngineConfig
from engine.types import EvaluationResult, ProbabilityDistribution, ProbabilityModel
from engine.windows import eligible_windows

PROBABILITY_FLOOR = 1e-12


def rank_digits(distribution: ProbabilityDistribution) -> tuple[int, ...]:
    if len(distribution) != 10:
        raise ValueError("distribution must contain ten probabilities")
    if any(value < 0 for value in distribution):
        raise ValueError("distribution cannot contain negative probabilities")
    total = sum(distribution)
    if not math.isclose(total, 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(f"distribution must sum to 1, got {total}")
    return tuple(sorted(range(10), key=lambda digit: (-distribution[digit], digit)))


def _longest_miss_streak(hit_flags: Sequence[bool]) -> int:
    longest = 0
    current = 0
    for hit in hit_flags:
        if hit:
            current = 0
        else:
            current += 1
            longest = max(longest, current)
    return longest


def evaluate_model(
    model: ProbabilityModel,
    results: Sequence[str],
    *,
    position: int,
    window: int,
    horizon: int,
    config: EngineConfig,
) -> EvaluationResult:
    if position not in range(4):
        raise ValueError("position must be between 0 and 3")

    first_target = max(config.min_train_size, len(results) - horizon)
    hit_flags: list[bool] = []
    actual_probabilities: list[float] = []
    log_losses: list[float] = []
    brier_scores: list[float] = []

    for target_index in range(first_target, len(results)):
        training_start = max(0, target_index - window)
        training = results[training_start:target_index]
        if len(training) < config.min_train_size:
            continue

        distribution = model.predict(training, position)
        ranking = rank_digits(distribution)
        actual = int(results[target_index][position])
        hit_flags.append(actual in ranking[: config.top_k])

        actual_probability = max(distribution[actual], PROBABILITY_FLOOR)
        actual_probabilities.append(actual_probability)
        log_losses.append(-math.log(actual_probability))
        brier_scores.append(
            sum(
                (probability - (1.0 if digit == actual else 0.0)) ** 2
                for digit, probability in enumerate(distribution)
            )
        )

    sample_size = len(hit_flags)
    if sample_size == 0:
        raise ValueError("evaluation produced zero samples")

    hits = sum(hit_flags)
    hit_rate = hits / sample_size
    recent_flags = hit_flags[-config.recent_eval_size :]
    baseline_hit_rate = theoretical_top_k_hit_rate(config.top_k)

    return EvaluationResult(
        model_name=model.name,
        position=position,
        window=window,
        horizon=horizon,
        sample_size=sample_size,
        top_k=config.top_k,
        hits=hits,
        hit_rate=hit_rate,
        baseline_hit_rate=baseline_hit_rate,
        lift=hit_rate - baseline_hit_rate,
        recent_hit_rate=sum(recent_flags) / len(recent_flags),
        longest_miss_streak=_longest_miss_streak(hit_flags),
        mean_actual_probability=sum(actual_probabilities) / sample_size,
        log_loss=sum(log_losses) / sample_size,
        brier_score=sum(brier_scores) / sample_size,
    )


def evaluate_market(
    results: Sequence[str],
    models: Iterable[ProbabilityModel],
    config: EngineConfig,
) -> list[EvaluationResult]:
    evaluations: list[EvaluationResult] = []
    for horizon in config.eval_horizons:
        windows = eligible_windows(
            len(results),
            config.windows,
            min_train_size=config.min_train_size,
            evaluation_horizon=horizon,
        )
        for window in windows:
            for model in models:
                for position in range(4):
                    evaluations.append(
                        evaluate_model(
                            model,
                            results,
                            position=position,
                            window=window,
                            horizon=horizon,
                            config=config,
                        )
                    )
    return evaluations


def candidate_rank_key(result: EvaluationResult) -> tuple[float | int | str, ...]:
    return (
        result.lift,
        result.sample_size,
        result.recent_hit_rate,
        result.mean_actual_probability,
        -result.log_loss,
        -result.brier_score,
        result.window,
        result.horizon,
        result.model_name,
    )


def select_best_by_position(
    evaluations: Iterable[EvaluationResult],
) -> dict[int, EvaluationResult]:
    best: dict[int, EvaluationResult] = {}
    for evaluation in evaluations:
        current = best.get(evaluation.position)
        if current is None or candidate_rank_key(evaluation) > candidate_rank_key(current):
            best[evaluation.position] = evaluation
    return best
