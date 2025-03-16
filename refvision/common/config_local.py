# refvision/common/config_local.py
"""
local configuration
"""
from refvision.common.config_base import Config, BASE_DIR, CONFIG_YAML_PATH
import os
import yaml


if not os.path.exists(CONFIG_YAML_PATH):
    raise FileNotFoundError(f"Config file not found: {CONFIG_YAML_PATH}")

with open(CONFIG_YAML_PATH) as file:
    CONFIG_YAML = yaml.safe_load(file)


class LocalConfig(Config):
    """
    local configuration
    """

    VIDEO_NAME = os.getenv("VIDEO_NAME", "theo_maddox_squat_2")
    PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
    VIDEOS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "raw_data"))
    DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw_data")

    os.makedirs(DATA_DIR, exist_ok=True)
    VIDEO_PATH = os.path.join(DATA_DIR, VIDEO_NAME)

    RAW_VIDEO_PATH = f"{VIDEO_PATH}.mp4"
    TEMP_DIR = os.path.join(PROJECT_ROOT, "temp_videos")
    TEMP_MP4_FILE = os.path.join(TEMP_DIR, f"{VIDEO_NAME}.mp4")

    OUTPUT_DIR = os.path.join(PROJECT_ROOT, "runs", "pose", "track")
    # os.makedirs(OUTPUT_DIR, exist_ok=True)

    OUTPUT_VIDEO_PATH = os.path.join(OUTPUT_DIR, f"{VIDEO_NAME}.avi")
    AVI_OUTPUT = os.path.join(OUTPUT_DIR, f"{VIDEO_NAME}.avi")
    MP4_OUTPUT = os.path.join(OUTPUT_DIR, f"{VIDEO_NAME}.mp4")

    MODEL_PT_PATH = os.path.join(PROJECT_ROOT, "model_zoo", "yolo11x-pose.pt")
    MODEL_ONNX_PATH = os.path.join(PROJECT_ROOT, "model_zoo", "yolo11x-pose.onnx")
    MODEL_ENGINE_PATH = os.path.join(PROJECT_ROOT, "model_zoo", "yolo11x-pose.engine")

    S3_BUCKET = os.getenv("TEST_S3_BUCKET", CONFIG_YAML.get("s3_bucket", "refvision"))
    S3_KEY = f"{VIDEO_NAME}.mp4"
    VIDEO_KEY = f"{VIDEO_NAME}.mp4"
    INGESTION_MODE = "simulated"
