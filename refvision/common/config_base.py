# refvision/common/config_base.py
"""
Global configuration for RefVision pipeline.
"""
import os
import pathlib
import yaml
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = pathlib.Path(__file__).resolve().parent
CONFIG_YAML_PATH = BASE_DIR / "config.yaml"

if not CONFIG_YAML_PATH.exists():
    raise FileNotFoundError(f"Config file not found: {CONFIG_YAML_PATH}")

with open(CONFIG_YAML_PATH) as file:
    CONFIG_YAML = yaml.safe_load(file)


class Config:
    """
    Common config, defaults
    """

    LEFT_HIP_IDX = 11
    RIGHT_HIP_IDX = 12
    LEFT_KNEE_IDX = 13
    RIGHT_KNEE_IDX = 14
    THRESHOLD = 0.0
    AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
    S3_BUCKET_RAW = CONFIG_YAML.get("s3_bucket_raw", "refvision-raw-videos")
    S3_BUCKET_ANNOTATED = CONFIG_YAML.get(
        "s3_bucket_annotated", "refvision-annotated-videos"
    )
    VIDEO_STREAM_NAME = CONFIG_YAML.get("video_stream_name", "RefVisionVideoStream")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    FLASK_APP_MODE = os.getenv("FLASK_APP_MODE", "Local")
    USERNAME = os.getenv("APP_USERNAME", "admin")
    PASSWORD = os.getenv("APP_PASSWORD", "secret")
    LIFTER_SELECTOR = CONFIG_YAML.get("LIFTER_SELECTOR", None)
