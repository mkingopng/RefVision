# refvision/model/model_compile.py
"""
This script is used to compile the model
 .pt -> ONNX -> TensorRT engine.

Usage:
    poetry run python refvision/model/model_compile.py
"""
import os

os.environ["CUDA_MODULE_LOADING"] = "LAZY"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # Ensure PyTorch can see the GPU
os.environ["TORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"  # Legacy flag
import torch
import tensorrt as trt
from ultralytics import YOLO
import subprocess
from refvision.common.config_local import LocalConfig


TRT_LOGGER = trt.Logger(trt.Logger.WARNING)


def check_cuda():
    """
    Ensure CUDA is available before proceeding.
    """
    print(f"DEBUG: Torch CUDA Available: {torch.cuda.is_available()}")

    # Force CUDA initialization early
    if torch.cuda.is_available():
        torch.cuda.init()

    num_devices = torch.cuda.device_count()
    print(f"DEBUG: Torch CUDA Device Count: {num_devices}")

    if num_devices == 0:
        print("DEBUG: No CUDA devices detected. Running nvidia-smi for diagnostics:")
        subprocess.run("nvidia-smi", shell=True)  # Show GPU processes
        raise RuntimeError(
            "❌ No CUDA devices found! Ensure your GPU is properly installed."
        )

    # Force setting CUDA device explicitly
    device_id = 0  # First available GPU
    torch.cuda.set_device(device_id)
    print(f"✅ Using CUDA Device {device_id}: {torch.cuda.get_device_name(device_id)}")


def convert_pt_to_onnx():
    """
    Converts YOLOv11 `.pt` file to `.onnx` format
    :return:
    """
    print(f"Converting {LocalConfig.MODEL_PT_PATH} to {LocalConfig.MODEL_ONNX_PATH}...")

    # prevent YOLO from forcing CPU-based `onnxruntime`
    subprocess.run(["pip", "uninstall", "-y", "onnxruntime"], check=True)
    subprocess.run(
        [
            "pip",
            "install",
            "--upgrade",
            "--extra-index-url",
            "https://pypi.ngc.nvidia.com",
            "onnxruntime-gpu",
        ],
        check=True,
    )

    # load YOLO model and explicitly use CUDA
    model = YOLO(LocalConfig.MODEL_PT_PATH)
    model.to("cuda")  # explicitly move model to CUDA before exporting
    model.export(format="onnx", dynamic=True, simplify=True, opset=12)
    print(f"✅ ONNX model saved at {LocalConfig.MODEL_ONNX_PATH}")


def convert_onnx_to_trt():
    """
    Converts `.onnx` file to TensorRT `.engine` format
    :return:
    """
    check_cuda()
    print(
        f"Converting {LocalConfig.MODEL_ONNX_PATH} to {LocalConfig.MODEL_ENGINE_PATH}..."
    )
    builder = trt.Builder(TRT_LOGGER)
    network = builder.create_network(
        1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
    )
    config = builder.create_builder_config()

    # enable FP16 only if supported
    if builder.platform_has_fast_fp16:
        config.set_flag(trt.BuilderFlag.FP16)
        print("✅ FP16 mode enabled for TensorRT optimization")

    config.max_workspace_size = 1 << 30  # 1GB workspace
    parser = trt.OnnxParser(network, TRT_LOGGER)
    with open(LocalConfig.MODEL_ONNX_PATH, "rb") as f:
        if not parser.parse(f.read()):
            print("❌ ERROR: Failed to parse ONNX model!")
            for i in range(parser.num_errors):
                print(parser.get_error(i))
            return

    engine = builder.build_engine(network, config)

    if engine is None:
        print("❌ ERROR: Failed to build TensorRT engine!")
        return

    with open(LocalConfig.MODEL_ENGINE_PATH, "wb") as f:
        f.write(engine.serialize())

    print(f"✅ TensorRT engine saved at {LocalConfig.MODEL_ENGINE_PATH}")


if __name__ == "__main__":
    convert_pt_to_onnx()
    convert_onnx_to_trt()
