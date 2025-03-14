# refvision/common/config_local.py
"""
local configuration
"""
from refvision.common.config_base import Config, BASE_DIR, config_yaml
import os


class LocalConfig(Config):
    """
    local configuration
    """

    VIDEO_NAME = os.getenv("VIDEO_NAME", "theo_maddox_squat_2")
    VIDEOS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "raw_data"))
    VIDEO_PATH = os.path.join(VIDEOS_DIR, VIDEO_NAME)
    RAW_VIDEO_PATH = f"{VIDEO_PATH}.mp4"
    TEMP_MP4_FILE = os.path.abspath(
        os.path.join(BASE_DIR, "..", "temp_videos", f"{VIDEO_NAME}.mp4")
    )
    OUTPUT_VIDEO_PATH = os.path.abspath(
        os.path.join(BASE_DIR, "..", "runs", "pose", "track", f"{VIDEO_NAME}.avi")
    )
    MODEL_PATH = os.path.join(BASE_DIR, "..", "model_zoo", "yolo11x-pose.pt")
    AVI_OUTPUT = os.path.join(
        BASE_DIR, "..", "runs", "pose", "track", f"{VIDEO_NAME}.avi"
    )
    MP4_OUTPUT = os.path.join(
        BASE_DIR, "..", "runs", "pose", "track", f"{VIDEO_NAME}.mp4"
    )
    S3_BUCKET = os.getenv("TEST_S3_BUCKET", config_yaml.get("s3_bucket", "refvision"))
    S3_KEY = f"{VIDEO_NAME}.mp4"
    INGESTION_MODE = "simulated"
