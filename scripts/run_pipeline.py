# scripts/run_pipeline.py
"""
RefVision Pipeline Runner
Steps:
    A) Convert raw input (MOV, etc.) to norm MP4 (no orientation metadata).
    1) YOLO inference -> produces an annotated .avi
    2) Convert .avi -> .mp4
    3) Upload .mp4 to S3
    4) Launch Gunicorn to serve Flask on specified port.
Usage: poetry run python -m scripts.run_pipeline
"""
import argparse
import subprocess
import os
import sys
import time
import webbrowser
import json
from typing import List
from config.config import CFG
from refvision.utils.aws_clients import get_s3_client
from refvision.ingestion.video_ingestor import get_video_ingestor
from refvision.utils.logging_setup import setup_logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logger = setup_logging(os.path.join(os.path.dirname(__file__), "../logs/pipeline.log"))


def run_command(cmd_list: List[str]) -> None:
    """
    Runs a shell command and logs the command before execution.
    :param cmd_list: List of command arguments.
    :return: None
    """
    logger.info(f"Running command: {' '.join(cmd_list)}")
    subprocess.check_call(cmd_list)


def normalize_video(input_video: str, output_video: str) -> None:
    """
    Converts the input video to a normalised MP4 (stripped of metadata).
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


def run_yolo_inference(video: str, model_path: str) -> None:
    """
    runs YOLO inference on the input video.
    :param video: path to the video file.
    :param model_path: path to the YOLO model weights.
    :return: None
    """
    logger.info("=== 1) YOLO Inference ===")
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


def launch_gunicorn(flask_port: str) -> None:
    """
    Launches the Gunicorn server for the Flask application.
    :param flask_port: Port on which to run the Gunicorn server.
    :return: None
    """
    logger.info("=== 4) Starting Gunicorn (Flask app) ===")
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


def save_decision_to_file(decision_data: dict) -> None:
    """
    Save the decision data (including decision, turnaround frame, and keypoints)
    to a text file.
    :param decision_data: Dictionary containing the decision details.
    :return: None
    """
    decision_file = "/tmp/decision.json"  # todo: change this to dynamodb

    # Open the file in append mode to add new data without overwriting
    with open(decision_file, "w") as f:
        f.write(json.dumps(decision_data))
    logger.info(f"Decision data saved to {decision_file}")


def run_pipeline() -> None:
    """
    Orchestrates the RefVision pipeline by executing the following steps:
      A) Normalize input video to MP4.
      B) Run YOLO inference on the normalized video.
      C) Convert the resulting AVI to MP4.
      D) Upload the final MP4 to S3.
      E) Launch Gunicorn to serve the Flask application.
    Command-line arguments override default configuration values.
    :return: None
    """
    parser = argparse.ArgumentParser(description="Orchestrate the RefVision pipeline")

    parser.add_argument("--video", default=None, help="Path to raw input video")
    parser.add_argument("--model-path", default=None, help="Path to YOLO model weights")
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
    video: str = args.video or CFG.VIDEO
    model_path: str = args.model_path or CFG.MODEL_PATH
    avi_output: str = args.avi_output or CFG.AVI_OUTPUT
    mp4_output: str = args.mp4_output or CFG.MP4_OUTPUT
    s3_bucket: str = args.s3_bucket or CFG.S3_BUCKET
    s3_key: str = args.s3_key or CFG.S3_KEY
    flask_port: str = args.flask_port or str(CFG.FLASK_PORT)

    # Initialize video ingestion
    ingestor = get_video_ingestor(CFG.TEMP_MP4_FILE, s3_bucket, s3_key)
    ingestor.ingest()

    # A: Normalize input video.
    normalize_video(video, CFG.TEMP_MP4_FILE)

    # B: Run YOLO inference.
    run_yolo_inference(CFG.TEMP_MP4_FILE, model_path)

    # read the file that the YOLO script created
    inference_json_path = "/tmp/inference_results.json"
    if os.path.exists(inference_json_path):
        with open(inference_json_path, "r") as f:
            results = json.load(f)
            print(results)
    else:
        logger.warning("No inference_results.json found; defaulting to empty.")

    # C: Convert AVI output to MP4.
    convert_avi_to_mp4(avi_output, mp4_output)

    # D: Upload final MP4 to S3.
    upload_video_to_s3(mp4_output, s3_bucket, s3_key)

    # 1) read the JSON that inference.py wrote
    inference_json_path = "/tmp/inference_results.json"
    if os.path.exists(inference_json_path):
        with open(inference_json_path, "r") as f:
            decision_data = json.load(f)
        logger.info(f"Decision data loaded from inference => {decision_data}")

        # 2) If you want to store or display it
        #    For example, you can keep 'save_decision_to_file' if you'd prefer
        #    to store it in /tmp/decision.json or upload it to S3
        save_decision_to_file(decision_data)
    else:
        logger.warning("No inference_results.json found; skipping decision data.")

    # G: Launch Gunicorn to serve the Flask application.
    launch_gunicorn(flask_port)


if __name__ == "__main__":
    run_pipeline()
    #  todo: bedrock -> good explanation
    #  todo: DynamoDB -> store of state
    #  todo: Step Functions -> orchestration
    #  todo: serverless inference
