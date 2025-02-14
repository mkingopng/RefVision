"""
Module for series utilities.
"""

from typing import Sequence, Optional, List


def smooth_series(
    values: Sequence[Optional[float]], window_size: int = 1
) -> List[Optional[float]]:
    """
    Smooths a series of hip position values using a simple moving average.
    :param values: A sequence of hip positions (or None).
    :param window_size: Size of the moving average window.
    :return: A list of smoothed values.
    """
    if window_size < 2:
        return list(values)  # Convert to list in case values is a Sequence

    smoothed: List[Optional[float]] = [None] * len(values)
    half_w = window_size // 2
    for i in range(len(values)):
        if values[i] is None:
            smoothed[i] = None
            continue
        # Filter out None values in the window
        local_vals = [
            v
            for j in range(i - half_w, i + half_w + 1)
            if 0 <= j < len(values) and (v := values[j]) is not None
        ]
        smoothed[i] = sum(local_vals) / len(local_vals) if local_vals else None
    return smoothed
