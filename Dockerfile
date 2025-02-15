FROM python:3.11-slim

# Install necessary system dependencies, including libgl and libglib.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry.
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
ENV PYTHONPATH="/app"

# Copy Poetry files and install dependencies.
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --without dev

# Copy your application code.
COPY . .

ENV MODEL_S3_PATH="s3://refvision-yolo-model/yolo11x-pose.pt"

EXPOSE 8080

CMD ["poetry", "run", "python", "refvision/inference/serve.py"]
