# refvision/utils/logging_setup.py
"""
module for centralized logging setup.
"""
import os
import logging
from typing import Optional


def setup_logging(log_file: Optional[str] = None):
    """
    configures logging for the application.
    if a log_file is provided, ensures its directory exists before creating a
    FileHandler.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Create and add a console handler.
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # If a log_file is provided, create its directory if needed and add a file handler.
    if log_file:
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        file_handler = logging.FileHandler(log_file, mode="w")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
