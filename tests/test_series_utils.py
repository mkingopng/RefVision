# tests/test_series_utils.py
"""
test smooth series in different scenarios
"""
from refvision.utils.series_utils import smooth_series


def test_smooth_series_no_window() -> None:
    """
    test smooth series no window
    :return: None
    """
    values = [1.0, 2.0, 3.0]
    result = smooth_series(values, window_size=1)
    assert result == values


def test_smooth_series_with_window() -> None:
    """
    test smooth series with window
    :return: None
    """
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = smooth_series(values, window_size=3)
    # For index 1, the average should be (1.0+2.0+3.0)/3 = 2.0.
    assert result[1] == 2.0


def test_smooth_series_with_none() -> None:
    """
    test smooth series with none
    :return: None
    """
    values = [None, 2.0, 3.0, None, 5.0]
    result = smooth_series(values, window_size=3)
    # For index 1, the average of available [2.0, 3.0] is 2.5.
    assert result[1] == 2.5
