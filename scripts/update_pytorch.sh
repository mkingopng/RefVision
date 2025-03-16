#!/bin/bash
set -e  # Stop on errors

echo "🛠️ Setting up the environment..."

# Install all dependencies EXCEPT Ultralytics to avoid Torch version conflicts
echo "🔧 Installing dependencies (excluding Ultralytics)..."
poetry install --without ultralytics

echo "🔄 Checking for PyTorch Nightly Updates..."
poetry run pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128 --no-deps

# Extract CUDA versions from installed PyTorch
TORCH_CUDA_VERSION=$(poetry run python -c "import torch; print(torch.version.cuda)")
echo "✅ PyTorch Installed with CUDA $TORCH_CUDA_VERSION"

# Define required CUDA versions
if [[ "$TORCH_CUDA_VERSION" == "12.8" ]]; then
    REQUIRED_CUDA_RUNTIME="nvidia-cuda-runtime-cu12==12.8.57"
    REQUIRED_CUBLAS="nvidia-cublas-cu12==12.8.3.14"
    REQUIRED_CUDNN="nvidia-cudnn-cu12==9.8.0.87"
else
    echo "⚠️ Unsupported CUDA version detected: $TORCH_CUDA_VERSION"
    exit 1
fi

echo "🔄 Installing CUDA Dependencies..."
poetry run pip install --force-reinstall \
    "$REQUIRED_CUDA_RUNTIME" \
    "$REQUIRED_CUBLAS" \
    "$REQUIRED_CUDNN"

echo "✅ CUDA Dependencies Installed"

# Install Ultralytics separately without dependencies to avoid conflicts
echo "🚀 Installing Ultralytics (without dependencies)..."
poetry run pip install ultralytics --no-deps

echo "✅ Environment setup complete!"
