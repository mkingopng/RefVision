#
"""
Model Loader for TensorRT Inference
"""
import os
import numpy as np
import torch
import tensorrt as trt
from ultralytics import YOLO
from typing import Tuple
import logging

# from refvision.utils.video_utils import load_video_frames

logger = logging.getLogger(__name__)


class YOLOTensorRTOutput:
    """
    Wrapper to format TensorRT outputs like YOLO detections.
    """

    def __init__(self, boxes: np.ndarray, keypoints: np.ndarray, conf: np.ndarray):
        self.boxes = torch.tensor(boxes) if len(boxes) > 0 else torch.empty((0, 4))
        self.keypoints = (
            torch.tensor(keypoints) if len(keypoints) > 0 else torch.empty((0, 17, 3))
        )  # assuming 17 keypoints
        self.conf = torch.tensor(conf) if len(conf) > 0 else torch.empty((0,))

        # assign YOLO-like attribute names
        self.xyxy = self.boxes  # bounding boxes in xyxy format
        self.scores = self.conf  # confidence scores


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
        logger.info("✅ TensorRT Engine loaded successfully.")

        self.setup_dynamic_shapes()

    def setup_dynamic_shapes(self):
        """
        Configures the TensorRT execution context to handle dynamic input shapes.
        """
        logger.info("🔧 Configuring dynamic shape bindings...")

        for idx in range(self.engine.num_io_tensors):
            name = self.engine.get_tensor_name(idx)
            shape = self.engine.get_tensor_shape(name)

            if -1 in shape:
                fixed_shape = (
                    1,
                    3,
                    640,
                    640,
                )  # Adjust based on YOLO model expectations
                self.context.set_input_shape(name, fixed_shape)
                logger.info(f"✅ Set dynamic shape {shape} -> {fixed_shape} for {name}")

    def infer(self, inputs: torch.Tensor) -> YOLOTensorRTOutput:
        """
        Perform inference using TensorRT engine.
        :param inputs: Input tensor (image frame)
        :return: Model output formatted like YOLO predictions
        """
        num_bindings = self.engine.num_io_tensors
        bindings = [None] * num_bindings
        tensor_names = [self.engine.get_tensor_name(i) for i in range(num_bindings)]

        for idx, name in enumerate(tensor_names):
            dtype = (
                torch.float16
                if self.engine.get_tensor_dtype(name) == trt.DataType.HALF
                else torch.float32
            )
            shape = tuple(self.context.get_tensor_shape(name))

            if -1 in shape:
                raise RuntimeError(
                    f"🚨 ERROR: Invalid shape {shape} detected for tensor '{name}'. Check optimization profile!"
                )

            bindings[idx] = torch.empty(size=shape, dtype=dtype, device=self.device)

        # Copy input to device
        inputs = inputs.to(self.device)

        # Run inference
        self.context.execute_v2([binding.data_ptr() for binding in bindings])  # type: ignore

        # Process output tensor and return in YOLO format
        return self.format_yolo_output(bindings[-1])

    def format_yolo_output(self, output_tensor: torch.Tensor) -> YOLOTensorRTOutput:
        """
        Convert raw TensorRT model output into YOLO-compatible format.
        :param output_tensor:
        :return:
        """
        output_array = output_tensor.cpu().numpy()

        if output_array.shape[0] == 0:
            return YOLOTensorRTOutput(
                np.empty((0, 4)), np.empty((0, 17, 3)), np.empty((0,))
            )

        # Extract bounding boxes, keypoints, and confidence scores
        boxes = output_array[:, :4]  # First 4 values are bounding boxes
        keypoints = output_array[:, 4:-1].reshape((-1, 17, 3))  # Assuming 17 keypoints
        conf = output_array[:, -1]  # Confidence score (last column)

        return YOLOTensorRTOutput(boxes, keypoints, conf)


def load_model(model_path: str) -> Tuple[object, torch.device]:
    """
    Loads a PyTorch YOLO model or a TensorRT Engine.
    :param model_path: (str) Path to the model file (.pt or .engine).
    :returns: Tuple[object, torch.device] The loaded model and the device.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"🖥️ Using device: {device}")

    if not os.path.exists(model_path):
        logger.error(f"❌ Model file {model_path} does not exist.")
        raise FileNotFoundError(f"Model file {model_path} does not exist.")

    if model_path.endswith(".engine"):
        model = TensorRTModel(model_path, device)

        # Remove unnecessary attributes
        logger.info(f"🛠️ Loading TensorRT model from {model_path}...")
        model = TensorRTModel(model_path, device)
        logger.info("✅ TensorRT Model Loaded Successfully.")

    else:
        logger.info(f"🛠️ Loading PyTorch model from {model_path}...")
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
