# refvision/inference/model_loader.py
"""
Module for loading the YOLO model.
"""
import os
from ultralytics import YOLO
from typing import Tuple
import logging
import torch


logger = logging.getLogger(__name__)


def load_model(model_path: str) -> Tuple[YOLO, torch.device]:
    """
    Loads the YOLO model from the specified path and sets up the device.
    :param model_path: (str) Path to the YOLO weights.
    :returns: Tuple[YOLO, torch.device] The loaded model and the device used.
    :raises: FileNotFoundError If the model file does not exist.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    if not os.path.exists(model_path):
        logger.error(f"Model file {model_path} does not exist.")
        raise FileNotFoundError(f"Model file {model_path} does not exist.")

    model = YOLO(model_path)
    model.overrides["verbose"] = True

    model.fuse()

    # torch.compile
    compiled_model = torch.compile(model.model, mode="max-autotune")
    # fp16
    compiled_model = compiled_model.to(dtype=torch.float16, device=device)

    model.model = compiled_model
    return model, device
