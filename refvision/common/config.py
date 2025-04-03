# refvision/common/config.py
"""
Unified configuration for RefVision pipeline, combining local/cloud logic.
"""

import os
import yaml
from dotenv import load_dotenv

# 1) load .env file if present
load_dotenv()

# 2) paths
BASE_DIR = os.path.dirname(__file__)
CONFIG_YAML_PATH = os.path.join(BASE_DIR, "config.yaml")

if not os.path.exists(CONFIG_YAML_PATH):
    raise FileNotFoundError(f"Config file not found: {CONFIG_YAML_PATH}")

with open(CONFIG_YAML_PATH) as f:
    config_data = yaml.safe_load(f)

# 3) detect environment mode from environment variable, default "local"
ENV_MODE = os.getenv("REFVISION_ENV", "local").lower()


def get_config():
    """
    Build and return a unified config dict.
    Local vs. cloud is determined by REFVISION_ENV=local|cloud
    """

    # ---------- default keys ----------
    config = {}

    # environment / mode
    config["ENV_MODE"] = ENV_MODE

    # possibly keep FLASK_APP_MODE for backward compatibility
    config["FLASK_APP_MODE"] = os.getenv("FLASK_APP_MODE", "Local")

    # AWS Region & App Credentials
    config["AWS_REGION"] = os.getenv("AWS_REGION", "ap-southeast-2")
    config["APP_USERNAME"] = os.getenv("APP_USERNAME", "admin")
    config["APP_PASSWORD"] = os.getenv("APP_PASSWORD", "secret")

    # keypoint indexes
    config["LEFT_HIP_IDX"] = 11
    config["RIGHT_HIP_IDX"] = 12
    config["LEFT_KNEE_IDX"] = 13
    config["RIGHT_KNEE_IDX"] = 14

    # threshold for squat depth
    config["THRESHOLD"] = 0.0

    # port
    config["FLASK_PORT"] = int(os.getenv("FLASK_PORT", 5000))

    # aws credentials
    config["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID")
    config["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY")
    config["AWS_ENDPOINT_URL"] = None

    # grab default from config.yaml (LIFTER_SELECTOR, etc.)
    config["LIFTER_SELECTOR"] = config_data.get("LIFTER_SELECTOR", None)
    config["S3_BUCKET_RAW"] = config_data.get("s3_bucket_raw", "refvision-raw-videos")
    config["S3_BUCKET_ANNOTATED"] = config_data.get(
        "s3_bucket_annotated", "refvision-annotated-videos"
    )

    # dynamoDB
    config["AWS_ENDPOINT_URL"] = None
    config["DYNAMODB_TABLE"] = os.getenv("DYNAMODB_TABLE", "StateStore")

    # VIDEO_STREAM_NAME (for Kinesis Video usage)
    config["VIDEO_STREAM_NAME"] = os.getenv(
        "VIDEO_STREAM_NAME",
        config_data.get("video_stream_name", "RefVisionVideoStream"),
    )

    # ---------- local vs. cloud ----------
    if ENV_MODE == "local":
        # ---------- local-only configuration ----------
        project_root = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
        config["PROJECT_ROOT"] = project_root

        # create local directories
        data_dir = os.path.join(project_root, "data", "raw_data")
        temp_dir = os.path.join(project_root, "temp_videos")
        output_dir = os.path.join(project_root, "runs", "pose")
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        config["DATA_DIR"] = data_dir
        config["TEMP_DIR"] = temp_dir
        config["OUTPUT_DIR"] = output_dir

        # local default video name
        video_name = os.getenv("VIDEO_NAME", "theo_maddox_squat_2")
        config["VIDEO_NAME"] = video_name

        config["RAW_VIDEO_FILENAME"] = os.getenv("VIDEO_FILENAME", f"{video_name}.mp4")
        config["RAW_VIDEO_PATH"] = os.path.join(data_dir, config["RAW_VIDEO_FILENAME"])
        config["TEMP_MP4_FILE"] = os.path.join(temp_dir, f"{video_name}.mp4")
        config["AVI_OUTPUT"] = os.path.join(output_dir, f"{video_name}.avi")
        config["MP4_OUTPUT"] = os.path.join(output_dir, f"{video_name}.mp4")

        # model path
        config["MODEL_PATH"] = os.path.join(
            project_root, "model_zoo", "yolo11x-pose.pt"
        )

        # local S3 usage
        config["INGESTION_MODE"] = "simulated"
        config["S3_BUCKET"] = os.getenv(
            "TEST_S3_BUCKET", config_data.get("s3_bucket", "refvision")
        )
        config["S3_KEY"] = f"{video_name}.mp4"
        config["VIDEO_KEY"] = f"{video_name}.mp4"

        # additional local buckets
        config["RAW_BUCKET"] = os.getenv("RAW_BUCKET", "refvision-raw-videos")
        config["NORMALIZED_BUCKET"] = os.getenv(
            "NORMALIZED_BUCKET", "refvision-normalized-videos"
        )
        config["PROCESSED_BUCKET"] = os.getenv(
            "PROCESSED_BUCKET", "refvision-processed-videos"
        )

        # optional separate S3 keys
        config["RAW_KEY"] = f"incoming/{video_name}.mov"
        config["NORMALIZED_KEY"] = f"normalized/{video_name}.mp4"
        config["PROCESSED_KEY"] = f"processed/{video_name}annotated_output.mp4"
        config["DYNAMODB_TABLE"] = os.getenv("DYNAMODB_TABLE", "StateStore")

    elif ENV_MODE == "cloud":
        # ---------- cloud-only configuration ----------
        config["S3_BUCKET"] = os.getenv("S3_BUCKET", "refvision-annotated-videos")
        config["INGESTION_MODE"] = os.getenv("INGESTION_MODE", "simulated")

        # possibly override the default S3_BUCKET_RAW from YAML if you want:
        # config["S3_BUCKET_RAW"] = os.getenv("S3_BUCKET_RAW", config["S3_BUCKET_RAW"])

        config["AWS_ENDPOINT_URL"] = os.getenv("AWS_ENDPOINT_URL", None)
        config["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID")
        config["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY")
        config["DYNAMODB_TABLE"] = os.getenv("DYNAMODB_TABLE", "StateStore")

        # code references a separate raw S3 key for cloud:
        # config["S3_KEY_RAW"] = os.getenv("VIDEO_KEY", "incoming/raw_video.mp4")

    else:
        raise ValueError(
            f"Unknown REFVISION_ENV={ENV_MODE}, expected 'local' or 'cloud'."
        )

    # ---------- return the final dictionary ----------
    return config
