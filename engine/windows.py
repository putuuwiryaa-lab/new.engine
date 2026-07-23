from __future__ import annotations


def eligible_windows(
    history_size: int,
    requested_windows: tuple[int, ...],
    *,
    min_train_size: int,
    evaluation_horizon: int,
) -> tuple[int, ...]:
    available_training = history_size - evaluation_horizon
    if available_training < min_train_size:
        return ()

    eligible = tuple(
        window
        for window in requested_windows
        if min_train_size <= window <= available_training
    )
    if eligible:
        return eligible

    return (available_training,)
