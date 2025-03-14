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

environment = "local"  # or "cloud"
# class CFG:
if environment == "local":

    class CFG:
        # VIDEO_NAME = "jessica_good_lift"
        # VIDEO_NAME = "a_woman_squatting"
        # VIDEO_NAME = "theo_maddox_deadlift_2"
        VIDEO_NAME = "theo_maddox_squat_2"

        VIDEOS_DIR = os.path.join(BASE_DIR, "..", "data", "raw_data")
        VIDEO = os.path.join(
            BASE_DIR, "..", "data", "raw_data", f"{VIDEO_NAME}.mp4"
        )  # fix_me
        MODEL_PATH = os.path.join(BASE_DIR, "..", "model_zoo", "yolo11x-pose.pt")
        AVI_OUTPUT = os.path.join(
            BASE_DIR, "..", "runs", "pose", "track", f"{VIDEO_NAME}.avi"
        )  # fix_me
        TEMP_MP4_FILE = os.path.abspath(
            os.path.join(BASE_DIR, "..", "temp_videos", f"{VIDEO_NAME}.mp4")
        )  # fix_me
        MP4_OUTPUT = os.path.join(
            BASE_DIR, "..", "runs", "pose", "track", f"{VIDEO_NAME}.mp4"
        )  # fix_me
        MP4_FILE = f"{VIDEO_NAME}.mp4"
        S3_BUCKET = os.getenv(
            "TEST_S3_BUCKET", config_data.get("s3_bucket", "refvision")
        )
        S3_KEY = f"{VIDEO_NAME}.mp4"
        # S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "refvision")
        FLASK_PORT = 5000
        FLASK_APP_MODE = "Local"  # local or cloud
        lifter_selector = config_data.get(
            "lifter_selector", None
        )  # Load lifter selector from config.yaml
        AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
        AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
        AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
        VIDEO_KEY = os.environ.get("VIDEO_KEY", f"{VIDEO_NAME}.mp4")
        USERNAME = os.environ.get("APP_USERNAME", "admin")
        PASSWORD = os.environ.get("APP_PASSWORD", "secret")

else:

    class CFGCloud:
        # Load from .env or fallback to config.yaml
        S3_BUCKET = os.getenv(
            "TEST_S3_BUCKET", config_data.get("s3_bucket", "refvision-annotated-videos")
        )
        FLASK_PORT = 8080
        FLASK_APP_MODE = "cloud"
