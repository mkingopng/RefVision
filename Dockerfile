# Dockerfile
FROM python:3.11-slim

# Install necessary system dependencies.
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

# Copy environment file.
COPY .env ./
ENV PYTHONPATH="/app"

# Copy Poetry files and install dependencies.
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --without dev

# Copy the rest of the application code.
COPY . .

# Set environment variable for your model path.
ENV MODEL_S3_PATH="s3://refvision-yolo-model/yolo11x-pose.tar.gz"

# Expose the necessary port.
EXPOSE 8080

# Set the entrypoint to run your app.
ENTRYPOINT ["poetry", "run", "python", "unified_app.py"]

# Set default command (can be overridden by command line arguments).
CMD ["serve"]
