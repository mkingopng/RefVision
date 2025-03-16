#!/bin/bash
set -e  # Stop on errors

echo "🛠️ Starting model compilation..."

# Ensure CUDA is properly set up
echo "🔍 Checking CUDA availability..."
poetry run python -c "
import torch
if not torch.cuda.is_available():
    raise RuntimeError('❌ CUDA is not available! Ensure your GPU is detected.')
print('✅ CUDA is available. Detected:', torch.cuda.get_device_name(0))
"

# Step 1: Convert .pt to .onnx
echo "🔄 Converting YOLOv11 .pt model to .onnx..."
poetry run python -c "
from ultralytics import YOLO
from refvision.common.config_local import LocalConfig
print(f'Converting {LocalConfig.MODEL_PT_PATH} to {LocalConfig.MODEL_ONNX_PATH}...')
model = YOLO(LocalConfig.MODEL_PT_PATH)
model.to('cuda')
model.export(format='onnx', dynamic=True, simplify=True, opset=12)
print(f'✅ ONNX model saved at {LocalConfig.MODEL_ONNX_PATH}')
"

# Step 2: Convert .onnx to .engine (TensorRT)
echo "⚡ Converting ONNX to TensorRT..."
poetry run python -c "
import tensorrt as trt
import torch
from refvision.common.config_local import LocalConfig

print('🔍 Checking CUDA setup for TensorRT...')
if not torch.cuda.is_available():
    raise RuntimeError('❌ CUDA is not available for TensorRT!')
print(f'✅ Using CUDA device: {torch.cuda.get_device_name(0)}')

TRT_LOGGER = trt.Logger(trt.Logger.WARNING)
builder = trt.Builder(TRT_LOGGER)
network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
config = builder.create_builder_config()

if builder.platform_has_fast_fp16:
    config.set_flag(trt.BuilderFlag.FP16)
    print('✅ FP16 mode enabled for TensorRT optimization')

config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 1 << 30)  # 1GB workspace
parser = trt.OnnxParser(network, TRT_LOGGER)

with open(LocalConfig.MODEL_ONNX_PATH, 'rb') as f:
    if not parser.parse(f.read()):
        print('❌ ERROR: Failed to parse ONNX model!')
        for i in range(parser.num_errors):
            print(parser.get_error(i))
        exit(1)

# ✅ **Define Optimization Profile for Dynamic Input Shapes**
profile = builder.create_optimization_profile()
input_name = network.get_input(0).name  # Get first input name
profile.set_shape(input_name, (1, 3, 640, 640), (1, 3, 1280, 1280), (1, 3, 1920, 1920))  # min/opt/max shapes
config.add_optimization_profile(profile)

serialized_engine = builder.build_serialized_network(network, config)

if serialized_engine is None:
    print('❌ ERROR: Failed to build TensorRT engine!')
    exit(1)

with open(LocalConfig.MODEL_ENGINE_PATH, 'wb') as f:
    f.write(serialized_engine)

print(f'✅ TensorRT engine saved at {LocalConfig.MODEL_ENGINE_PATH}')
"

echo "🎉 Model compilation complete!"
