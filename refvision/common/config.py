# refvision/common/config.py
"""
Unified configuration for RefVision pipeline, combining local/cloud logic.
"""
import os
import yaml
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(__file__)
CONFIG_YAML_PATH = os.path.join(BASE_DIR, "config.yaml")

if not os.path.exists(CONFIG_YAML_PATH):
    raise FileNotFoundError(f"Config file not found: {CONFIG_YAML_PATH}")

with open(CONFIG_YAML_PATH) as f:
    config_data = yaml.safe_load(f)


def get_config():
    """
    Build and return a unified config dict.
    Local vs. cloud is determined by REFVISION_ENV=local|cloud
    """
    # 1) read environment every time
    env_mode = os.getenv("REFVISION_ENV", "local").lower()

    config = {}
    config["ENV_MODE"] = env_mode

    # possibly keep FLASK_APP_MODE for backward compatibility
    config["FLASK_APP_MODE"] = os.getenv("FLASK_APP_MODE", "Local")

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

    # AWS creds
    config["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID")
    config["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY")
    config["AWS_ENDPOINT_URL"] = None

    # from config.yaml
    config["LIFTER_SELECTOR"] = config_data.get("LIFTER_SELECTOR")
    config["S3_BUCKET_RAW"] = config_data.get("s3_bucket_raw", "refvision-raw-videos")
    config["S3_BUCKET_ANNOTATED"] = config_data.get(
        "s3_bucket_annotated", "refvision-annotated-videos"
    )
    config["DYNAMODB_TABLE"] = os.getenv("DYNAMODB_TABLE", "StateStore")

    # video stream name
    config["VIDEO_STREAM_NAME"] = os.getenv(
        "VIDEO_STREAM_NAME",
        config_data.get("video_stream_name", "RefVisionVideoStream"),
    )

    if env_mode == "local":
        project_root = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
        config["PROJECT_ROOT"] = project_root

        data_dir = os.path.join(project_root, "data", "raw_data")
        temp_dir = os.path.join(project_root, "temp_videos")
        output_dir = os.path.join(project_root, "runs", "pose")
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        config["DATA_DIR"] = data_dir
        config["TEMP_DIR"] = temp_dir
        config["OUTPUT_DIR"] = output_dir

        video_name = os.getenv("VIDEO_NAME", "andrew_olm_squat_2")
        config["VIDEO_NAME"] = video_name

        config["RAW_VIDEO_FILENAME"] = os.getenv("VIDEO_FILENAME", f"{video_name}.mp4")
        config["RAW_VIDEO_PATH"] = os.path.join(data_dir, config["RAW_VIDEO_FILENAME"])
        config["TEMP_MP4_FILE"] = os.path.join(temp_dir, f"{video_name}.mp4")
        config["AVI_OUTPUT"] = os.path.join(output_dir, "track", f"{video_name}.avi")
        config["MP4_OUTPUT"] = os.path.join(output_dir, f"{video_name}.mp4")
        config["MODEL_PATH"] = os.path.join(
            project_root, "model_zoo", "yolo11x-pose.pt"
        )

        config["INGESTION_MODE"] = "simulated"
        config["S3_BUCKET"] = os.getenv(
            "TEST_S3_BUCKET", config_data.get("s3_bucket", "refvision")
        )
        config["S3_KEY"] = f"{video_name}.mp4"
        config["VIDEO_KEY"] = f"{video_name}.mp4"

        config["RAW_BUCKET"] = os.getenv("RAW_BUCKET", "refvision-raw-videos")
        config["NORMALIZED_BUCKET"] = os.getenv(
            "NORMALIZED_BUCKET", "refvision-normalized-videos"
        )
        config["PROCESSED_BUCKET"] = os.getenv(
            "PROCESSED_BUCKET", "refvision-processed-videos"
        )

        config["RAW_KEY"] = f"incoming/{video_name}.mov"
        config["NORMALIZED_KEY"] = f"normalized/{video_name}.mp4"
        config["PROCESSED_KEY"] = f"processed/{video_name}.mp4"
        config["DYNAMODB_TABLE"] = os.getenv("DYNAMODB_TABLE", "StateStore")

    elif env_mode == "cloud":
        config["S3_BUCKET"] = os.getenv("S3_BUCKET", "refvision-annotated-videos")
        config["INGESTION_MODE"] = os.getenv("INGESTION_MODE", "simulated")
        config["AWS_ENDPOINT_URL"] = os.getenv("AWS_ENDPOINT_URL", None)
        config["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID")
        config["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY")
        config["DYNAMODB_TABLE"] = os.getenv("DYNAMODB_TABLE", "StateStore")

        # config["S3_BUCKET_RAW"] = os.getenv("S3_BUCKET_RAW", config["S3_BUCKET_RAW"])
        # config["S3_KEY_RAW"] = os.getenv("VIDEO_KEY", "incoming/raw_video.mp4")
    else:
        raise ValueError(
            f"Unknown REFVISION_ENV={env_mode}, expected 'local' or 'cloud'."
        )

    return config
