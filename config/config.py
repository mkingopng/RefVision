# config/config.py
"""
Global configuration for RefVision pipeline.
"""

import os
import yaml

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # This is the config/ directory

# Path to the YAML config file (assumed to be in the same directory as config.py)
CONFIG_YAML_PATH = os.path.join(BASE_DIR, "config.yaml")

# Load the YAML file
with open(CONFIG_YAML_PATH, "r") as f:
    config_data = yaml.safe_load(f)

class CFG:
    # Define other configuration variables as before.
    TEMP_VIDEOS_DIR = os.path.join(BASE_DIR, "..", "temp_videos")
    VIDEO = os.path.join(BASE_DIR, "..", "data", "raw_data", "theo_maddox_squat_2.mp4")
    MODEL_PATH = os.path.join(BASE_DIR, "..", "model_zoo", "yolo11x-pose.pt")
    AVI_OUTPUT = os.path.join(BASE_DIR, "..", "runs", "pose", "track", "theo_maddox_squat_2.avi")
    TEMP_MP4_FILE = os.path.join(TEMP_VIDEOS_DIR, "theo_maddox_squat_2.mp4")
    MP4_OUTPUT = os.path.join(BASE_DIR, "..", "runs", "pose", "track", "theo_maddox_squat_2.mp4")
    MP4_FILE = "theo_maddox_squat_2.mp4"
    S3_BUCKET = "refvision-annotated-videos"
    S3_KEY = "theo_maddox_squat_2.mp4"
    FLASK_PORT = 5000
    # Now load the lifter_selector from the YAML:
    lifter_selector = config_data.get("lifter_selector", None)
