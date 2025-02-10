# config/config.py
"""
Global configuration for RefVision pipeline.
"""
import os
import yaml

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CONFIG_YAML_PATH = os.path.join(BASE_DIR, "config.yaml")

with open(CONFIG_YAML_PATH, "r") as f:
    config_data = yaml.safe_load(f)

class CFG:
    # Define other configuration variables as before.
    VIDEO_NAME = "theo_maddox_squat_2"
    TEMP_VIDEOS_DIR = os.path.join(BASE_DIR, "..", "temp_videos")
    VIDEO = os.path.join(BASE_DIR, "..", "data", "raw_data", f"{VIDEO_NAME}.mp4")
    MODEL_PATH = os.path.join(BASE_DIR, "..", "model_zoo", "yolo11x-pose.pt")
    AVI_OUTPUT = os.path.join(BASE_DIR, "..", "runs", "pose", "track", f"{VIDEO_NAME}.avi")
    TEMP_MP4_FILE = os.path.join(TEMP_VIDEOS_DIR, f"{VIDEO_NAME}.mp4")
    MP4_OUTPUT = os.path.join(BASE_DIR, "..", "runs", "pose", "track", f"{VIDEO_NAME}.mp4")
    MP4_FILE = f"{VIDEO_NAME}.mp4"
    S3_BUCKET = "refvision-annotated-videos"
    S3_KEY = f"{VIDEO_NAME}.mp4"
    FLASK_PORT = 5000
    # Now load the lifter_selector from the YAML:
    lifter_selector = config_data.get("lifter_selector", None)
