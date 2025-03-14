# refvision/utils/timer.py
"""

"""
import time
import os
from refvision.utils.logging_setup import setup_logging

logger = setup_logging(
    os.path.join(os.path.dirname(__file__), "../../logs/timer_logs.log")
)


def measure_time(func):
    """
    Decorator function to measure execution time.
    Logs the time taken by the decorated function.
    """

    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        logger.info(f"Execution Time for {func.__name__}: {elapsed_time:.2f} seconds")
        return result

    return wrapper
