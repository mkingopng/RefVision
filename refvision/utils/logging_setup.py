# refvision/utils/logging_setup.py
"""
Module for centralized logging setup.
"""

import logging
from logging import Logger


def setup_logging(
    log_file: str = "logs/debug.log", level: int = logging.DEBUG
) -> Logger:
    """
    Set up centralized logging configuration.

    Args:
        log_file (str): Path to the log file.
        level (int): Logging level.

    Returns:
        Logger: Configured logger.
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Clear existing handlers if any.
    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


# Optionally, set up logging immediately upon import.
setup_logging()
