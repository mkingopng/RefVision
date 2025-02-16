# config/config.py
"""
Global configuration for RefVision pipeline.
"""
import os
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_YAML_PATH = os.path.join(BASE_DIR, "config.yaml")

with open(CONFIG_YAML_PATH, "r") as f:
    config_data = yaml.safe_load(f)


class CFG:
    """
    Global configuration for RefVision
    """

    VIDEO_NAME = "theo_maddox_squat_2"

    VIDEOS_DIR = os.path.join(BASE_DIR, "..", "data", "raw_data")

    VIDEO = os.path.join(BASE_DIR, "..", "data", "raw_data", f"{VIDEO_NAME}.mp4")

    MODEL_PATH = os.path.join(BASE_DIR, "..", "model_zoo", "yolo11x-pose.pt")

    AVI_OUTPUT = os.path.join(
        BASE_DIR, "..", "runs", "pose", "track", f"{VIDEO_NAME}.avi"
    )

    TEMP_MP4_FILE = os.path.abspath(
        os.path.join(BASE_DIR, "..", "temp_videos", f"{VIDEO_NAME}.mp4")
    )

    MP4_OUTPUT = os.path.join(
        BASE_DIR, "..", "runs", "pose", "track", f"{VIDEO_NAME}.mp4"
    )

    MP4_FILE = f"{VIDEO_NAME}.mp4"

    # Load from .env or fallback to config.yaml
    S3_BUCKET = os.getenv(
        "TEST_S3_BUCKET", config_data.get("s3_bucket", "refvision-annotated-videos")
    )

    # S3_BUCKET = os.getenv(
    #     "TEST_S3_BUCKET",
    #     config_data.get("s3_bucket", "refvision")
    # )

    S3_KEY = f"{VIDEO_NAME}.mp4"

    # Flask API Port
    # FLASK_PORT = 5000
    FLASK_PORT = 8080

    # Load lifter selector from config.yaml
    lifter_selector = config_data.get("lifter_selector", None)
