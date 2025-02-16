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

# Create logs directory so our app can write log files.
RUN mkdir -p /app/logs

# Copy Poetry files and install dependencies.
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --without dev

# Copy the rest of the application code.
COPY . .
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY unified_app.py /app/

# Set environment variables.
ENV MODEL_S3_PATH="s3://refvision-yolo-model/yolo11x-pose.tar.gz"
ENV FLASK_APP_MODE=cloud

# Expose the necessary port.
EXPOSE 8080

# Set the entrypoint to run your app.
ENTRYPOINT ["/entrypoint.sh"]
CMD ["serve"]
