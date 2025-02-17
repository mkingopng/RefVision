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

# Copy the entrypoint script and make it executable.
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set environment variables.
ENV MODEL_S3_PATH="s3://refvision-yolo-model/yolo11x-pose.tar.gz"
# By default, set FLASK_APP_MODE to "cloud" for deployment; you can override it locally.
ENV FLASK_APP_MODE=cloud

# Expose the port (for cloud mode, your unified_app.py will run on port 8080)
EXPOSE 8080

# Set the entrypoint to run your app.
ENTRYPOINT ["/entrypoint.sh"]
CMD ["serve"]
