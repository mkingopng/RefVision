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
    Local development configuration.
    """

    # 1) PROJECT ROOT & DIRECTORIES
    PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

    # directory for raw data inputs
    DATA_DIR = os.path.join(PROJECT_ROOT, "data", "raw_data")
    os.makedirs(DATA_DIR, exist_ok=True)

    # directory for intermediate/temporary files (transcoded MP4, etc.)
    TEMP_DIR = os.path.join(PROJECT_ROOT, "temp_videos")
    os.makedirs(TEMP_DIR, exist_ok=True)

    # directory where YOLO outputs go (and final pipeline artifacts):
    OUTPUT_DIR = os.path.join(PROJECT_ROOT, "runs", "pose")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2) VIDEO NAME & PATHS
    VIDEO_NAME = os.getenv("VIDEO_NAME", "theo_maddox_squat_2")

    RAW_VIDEO_FILENAME = os.getenv("VIDEO_FILENAME", f"{VIDEO_NAME}.mov")

    RAW_VIDEO_PATH = os.path.join(DATA_DIR, RAW_VIDEO_FILENAME)

    # temporary MP4 file (normalized), e.g. "temp_videos/theo_maddox_squat_2.mp4"
    TEMP_MP4_FILE = os.path.join(TEMP_DIR, f"{VIDEO_NAME}.mp4")

    # YOLO output (AVI) and final MP4 – all in OUTPUT_DIR
    AVI_OUTPUT = os.path.join(OUTPUT_DIR, f"{VIDEO_NAME}.avi")
    MP4_OUTPUT = os.path.join(OUTPUT_DIR, f"{VIDEO_NAME}.mp4")

    # 3) MODEL FILES
    MODEL_PATH = os.path.join(PROJECT_ROOT, "model_zoo", "yolo11x-pose.pt")

    # 4) S3 / CLOUD CONFIG
    S3_BUCKET = os.getenv("TEST_S3_BUCKET", CONFIG_YAML.get("s3_bucket", "refvision"))
    S3_KEY = f"{VIDEO_NAME}.mp4"
    VIDEO_KEY = f"{VIDEO_NAME}.mp4"
    INGESTION_MODE = "simulated"

    # S3 BUCKETS
    RAW_BUCKET = os.getenv("RAW_BUCKET", "refvision-raw-videos")
    NORMALIZED_BUCKET = os.getenv("NORMALIZED_BUCKET", "refvision-normalized-videos")
    PROCESSED_BUCKET = os.getenv("PROCESSED_BUCKET", "refvision-processed-videos")

    # Optional: If you need default keys
    RAW_KEY = "incoming/some_file.mov"  # or however you name it
    NORMALIZED_KEY = "normalized/some_file.mp4"
    PROCESSED_KEY = "processed/annotated_output.mp4"
