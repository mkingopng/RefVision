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

# Import TensorRT if available
try:
    import tensorrt as trt

    logger.info(f"TensorRT version detected: {trt.__version__}")
    TENSORRT_AVAILABLE = True
except ImportError:
    trt = None
    TENSORRT_AVAILABLE = False
    logger.warning("TensorRT is NOT available!")


class TensorRTModel:
    """
    Wrapper for TensorRT Engine Inference
    """

    def __init__(self, engine_path: str, device: str = "cuda"):
        self.device = device
        self.logger = trt.Logger(trt.Logger.WARNING)

        with open(engine_path, "rb") as f:
            runtime = trt.Runtime(self.logger)
            self.engine = runtime.deserialize_cuda_engine(f.read())

        self.context = self.engine.create_execution_context()
        logger.info("TensorRT Engine loaded successfully.")

    def infer(self, inputs: torch.Tensor) -> torch.Tensor:
        """
        Perform inference using TensorRT engine.
        :param inputs: Input tensor
        :return: Model output tensor
        """
        # Allocate memory for inputs and outputs
        bindings = [None] * self.engine.num_bindings
        for idx in range(self.engine.num_bindings):
            dtype = (
                torch.float16
                if self.engine.get_binding_dtype(idx) == trt.float16
                else torch.float32
            )
            shape = tuple(self.engine.get_binding_shape(idx))
            bindings[idx] = torch.empty(size=shape, dtype=dtype, device=self.device)

        self.context.execute_v2([binding.data_ptr() for binding in bindings])  # type: ignore

        return bindings[-1]  # return last output tensor


def load_model(model_path: str) -> Tuple[object, torch.device]:
    """
    Loads a PyTorch YOLO model or a TensorRT Engine.
    :param model_path: (str) Path to the model file (.pt or .engine).
    :returns: Tuple[object, torch.device] The loaded model and the device.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    if not os.path.exists(model_path):
        logger.error(f"Model file {model_path} does not exist.")
        raise FileNotFoundError(f"Model file {model_path} does not exist.")

    if model_path.endswith(".engine"):
        if not TENSORRT_AVAILABLE:
            raise RuntimeError(
                "TensorRT is not installed but an .engine file is provided."
            )

        logger.info(f"Loading TensorRT model from {model_path}...")
        model = TensorRTModel(model_path, device)
        logger.info("TensorRT Model Loaded Successfully.")

    else:
        logger.info(f"Loading PyTorch model from {model_path}...")
        model = YOLO(model_path)
        model.overrides["verbose"] = True  # type: ignore

        model.fuse()  # type: ignore

        model.model = model.model.to(  # type: ignore
            dtype=torch.float16,
            device=device,
            memory_format=torch.channels_last,
            non_blocking=True,
        )

        # torch.compile for optimisation
        model.model = torch.compile(model.model, mode="max-autotune")  # type: ignore

    return model, device
