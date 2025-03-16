# scripts/run_pipeline.py
"""
RefVision Pipeline Runner
Steps:
    1) convert raw input (MOV, etc.) to norm MP4 (no orientation metadata).
    2) YOLO inference -> produces an annotated .avi
    3) generate decision data
    4) convert .avi -> .mp4
    5) upload .mp4 to S3
    6) generate Explanation with Bedrock
    7) launch Gunicorn to serve Flask on specified port.
Usage: poetry run python -m scripts.run_pipeline
"""
import argparse
import subprocess
import os
import sys
import time
import webbrowser
from typing import List
from refvision.common.config_local import LocalConfig
from refvision.utils.aws_clients import get_s3_client
from refvision.ingestion.video_ingestor import get_video_ingestor
from refvision.utils.logging_setup import setup_logging
from refvision.ingestion.lifter_data_ingestor import ingest_lifter_data
from refvision.dynamodb.db_handler import get_data
from refvision.explanation.explanation_generator import (
    generate_explanation,
    store_decision_in_dynamodb,
)
from refvision.common.config_base import CONFIG_YAML_PATH

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logger = setup_logging(os.path.join(os.path.dirname(__file__), "../logs/pipeline.log"))

config_path = CONFIG_YAML_PATH

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
inference_json_path = os.path.join(PROJECT_ROOT, "tmp", "inference_results.json")
lifter_info_json_path = os.path.join(PROJECT_ROOT, "tmp", "lifter_info.json")

print("📌 Paths set in run_pipeline.py:")
print(f"📝 INFERENCE_JSON_PATH: {inference_json_path}")
print(f"📝 LIFTER_INFO_PATH: {lifter_info_json_path}")


def run_command(cmd_list: List[str]) -> None:
    """
    runs a shell command and logs the command before execution.
    :param cmd_list: List of command arguments.
    :return: None
    """
    logger.info(f"Running command: {' '.join(cmd_list)}")
    subprocess.check_call(cmd_list)


def normalize_video(input_video: str, output_video: str) -> None:
    """
    converts the input video to a normalised MP4 (stripped of metadata).
    :param input_video: Path to the input video file.
    :param output_video: Path where the normalised video will be saved.
    :return: None
    """
    logger.info("=== Pre-step: Normalize input to MP4 ===")
    cmd: List[str] = [
        "ffmpeg",
        "-y",
        "-i",
        input_video,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-map_metadata",
        "-1",
        output_video,
    ]
    run_command(cmd)


def run_yolo_inference(
    video: str, model_path: str, meet_id: str, lifter: str, attempt_number: int
) -> None:
    """
    Runs YOLO inference on the input video.
    :param video: Path to the video file.
    :param model_path: Path to the YOLO model weights.
    :param meet_id: ID of the meet.
    :param lifter: Name or ID of the lifter.
    :param attempt_number: Attempt number.
    :return: None
    """
    logger.info("=== 3) Running YOLO Inference ===")
    cmd: List[str] = [
        "poetry",
        "run",
        "python",
        "-m",
        "refvision.inference.inference",
        "--video",
        video,
        "--model_path",
        model_path,
        "--meet_id",
        meet_id,
        "--lifter",
        lifter,
        "--attempt_number",
        str(attempt_number),
    ]
    run_command(cmd)


def convert_avi_to_mp4(avi_output: str, mp4_output: str) -> None:
    """
    Converts the AVI output from YOLO to MP4 and removes the AVI file.
    :param avi_output: Path to the AVI file.
    :param mp4_output: Path where the MP4 file will be saved.
    :return: None
    :raises SystemExit: If the AVI file does not exist.
    """
    logger.info("=== 2) Convert AVI to MP4 ===")
    if not os.path.exists(avi_output):
        logger.error(f"ERROR: Expected AVI file '{avi_output}' not found")
        sys.exit(1)
    cmd: List[str] = [
        "ffmpeg",
        "-y",
        "-i",
        avi_output,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        mp4_output,
    ]
    run_command(cmd)
    os.remove(avi_output)


def upload_video_to_s3(mp4_output: str, s3_bucket: str, s3_key: str) -> None:
    """
    Uploads the final MP4 video to S3 using the boto3 client, then removes the
    local file.
    :param mp4_output: Path to the MP4 video file.
    :param s3_bucket: S3 bucket name.
    :param s3_key: S3 key for the video file.
    :return: None
    :raises SystemExit: If the upload fails.
    """
    logger.info("=== 3) Upload MP4 to S3 ===")
    s3_client = get_s3_client()
    try:
        with open(mp4_output, "rb") as f:
            s3_client.upload_fileobj(
                f, s3_bucket, s3_key, ExtraArgs={"ContentType": "video/mp4"}
            )
        logger.info(f"Uploaded {mp4_output} to s3://{s3_bucket}/{s3_key}")
    except Exception as e:
        logger.error(f"ERROR: Upload failed: {e}")
        sys.exit(1)


def generate_explanation_from_decision(
    meet_id: str, lifter: str, attempt_number: int
) -> None:
    """
    Reads decision data from DynamoDB and generates a natural language explanation.
    :param meet_id: ID of the meet.
    :param lifter: Name or ID of the lifter.
    :param attempt_number: Attempt number.
    :return: None
    """
    logger.info("=== 6) Generating Explanation with Bedrock ===")

    # ✅ Fetch decision data from DynamoDB
    decision_data = get_data(meet_id, lifter, attempt_number)

    if not decision_data:
        logger.error("ERROR: No data found in DynamoDB.")
        sys.exit(1)

    # Generate explanation
    try:
        explanation = generate_explanation(decision_data, "prompt_template.txt")
    except Exception as e:
        logger.error(f"ERROR: Bedrock failed to generate explanation: {e}")
        explanation = "Explanation unavailable due to error."

    # Store explanation back in DynamoDB
    decision_data["explanation"] = explanation
    store_decision_in_dynamodb(meet_id, lifter, attempt_number, explanation)

    logger.info(f"✅ Explanation stored in DynamoDB: {explanation}")


def launch_gunicorn(flask_port: int) -> None:
    """
    Launches the Gunicorn server for the Flask application.
    :param flask_port: Port on which to run the Gunicorn server.
    :return: None
    """
    logger.info("=== 7) Starting Gunicorn (Flask app) ===")
    bind_address: str = f"0.0.0.0:{flask_port}"
    logger.info(f"Launching Gunicorn on {bind_address}...")
    cmd: List[str] = [
        "poetry",
        "run",
        "gunicorn",
        "refvision.web.flask_app:app",
        "--chdir",
        "refvision/web",
        "--bind",
        bind_address,
        "--workers",
        "2",
    ]
    logger.info(f"Spawning command: {' '.join(cmd)}")
    gunicorn_process = subprocess.Popen(cmd)
    time.sleep(3)
    url: str = f"http://127.0.0.1:{flask_port}"
    logger.info(f"Opening browser at {url}")
    webbrowser.open(url)
    gunicorn_process.wait()
    logger.info("Gunicorn process has exited. Pipeline complete")


def run_pipeline() -> None:
    """
    Orchestrates the RefVision pipeline by executing the following steps:
      1) Ingest the raw video file.
      2) Normalize input video to MP4 with no metadata.
      3) Run YOLO inference on the normalised video.
      4) Convert the resulting AVI to MP4.
      5) Upload the final MP4 to S3.
      6) Read the JSON decision file
      7) Launch Gunicorn to serve the Flask application.
    :return: None
    """
    parser = argparse.ArgumentParser(description="Orchestrate the RefVision pipeline")
    parser.add_argument("--video", default=None, help="Path to raw input video")
    parser.add_argument("--model-path", default=None, help="Path to YOLO model weights")
    parser.add_argument("--meet-id", required=True, help="Powerlifting meet ID")
    parser.add_argument("--lifter", required=True, help="Lifter's name or ID")
    parser.add_argument(
        "--attempt-number", type=int, required=True, help="Attempt number"
    )
    parser.add_argument(
        "--avi-output", default=None, help="Path where YOLO writes the AVI file"
    )
    parser.add_argument(
        "--mp4-output", default=None, help="Path for the converted MP4 file"
    )
    parser.add_argument(
        "--s3-bucket", default=None, help="S3 bucket for uploading final MP4"
    )
    parser.add_argument("--s3-key", default=None, help="S3 key for final MP4 in S3")
    parser.add_argument(
        "--flask-port", default=None, help="Port for Gunicorn Flask app"
    )

    args = parser.parse_args()

    # 1: Ingest lifter data
    ingest_lifter_data("tmp/lifter_info.json")

    # 2: Initialise video ingestion
    ingestor = get_video_ingestor(
        LocalConfig.TEMP_MP4_FILE, args.s3_bucket, args.s3_key
    )
    ingestor.ingest()

    # 3: Normalize input video.
    normalize_video(args.video, LocalConfig.TEMP_MP4_FILE)

    # 4: Run YOLO inference.
    run_yolo_inference(
        LocalConfig.TEMP_MP4_FILE,
        args.model_path,
        args.meet_id,
        args.lifter,
        args.attempt_number,
    )

    # 5: Convert AVI output to MP4.
    convert_avi_to_mp4(args.avi_output, args.mp4_output)

    # 6: Upload final MP4 to S3.
    upload_video_to_s3(args.mp4_output, args.s3_bucket, args.s3_key)

    # 7: Generate explanation from DynamoDB
    generate_explanation_from_decision(args.meet_id, args.lifter, args.attempt_number)

    # 8: Launch Gunicorn to serve the Flask application.
    launch_gunicorn(args.flask_port)


if __name__ == "__main__":
    run_pipeline()

    #  todo: bedrock -> good explanation
    #  todo: DynamoDB -> store of state
    #  todo: step Functions -> orchestration
    #  todo: serverless inference
