# scripts/run_pipeline.py
"""
RefVision Pipeline Runner
Steps:
    A) Convert any raw input (MOV, etc.) to a normalised MP4 (with no
       orientation metadata).
    1) YOLO inference -> produces an annotated .avi
    2) Convert .avi -> .mp4
    3) Upload .mp4 to S3
    4) Launch Gunicorn to serve Flask on specified port.
usage: poetry run python -m scripts.run_pipeline
"""
import argparse
import subprocess
import os
import sys
import time
import webbrowser
from typing import List

# Add the project root to sys.path so that we can import CFG, etc.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import CFG
from refvision.utils.aws_clients import s3_client
from refvision.ingestion.video_ingestor import get_video_ingestor

def run_command(cmd_list: List[str]) -> None:
    """Runs a shell command, printing it first."""
    print(f"Running: {' '.join(cmd_list)}")
    subprocess.check_call(cmd_list)

def normalize_video(input_video: str, output_video: str) -> None:
    """Converts the input video to a normalized MP4 (stripped of metadata)."""
    print("=== Pre-step: Normalize input to MP4 ===")
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_video,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-map_metadata", "-1",
        output_video
    ]
    run_command(cmd)

def run_yolo_inference(video: str, model_path: str) -> None:
    """Runs YOLO inference."""
    print("=== 1) YOLO Inference ===")
    cmd = [
        "poetry", "run", "python", "-m", "refvision.inference.inference",
        "--video", video,
        "--model_path", model_path
    ]
    run_command(cmd)

def convert_avi_to_mp4(avi_output: str, mp4_output: str) -> None:
    """Converts the AVI output from YOLO to MP4."""
    print("=== 2) Convert AVI to MP4 ===")
    if not os.path.exists(avi_output):
        print(f"ERROR: Expected AVI file '{avi_output}' not found")
        sys.exit(1)
    cmd = [
        "ffmpeg",
        "-y",
        "-i", avi_output,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        mp4_output
    ]
    run_command(cmd)
    os.remove(avi_output)

def upload_video_to_s3(mp4_output: str, s3_bucket: str, s3_key: str) -> None:
    """Uploads the final MP4 to S3 using the boto3 client."""
    print("=== 3) Upload MP4 to S3 ===")
    try:
        with open(mp4_output, 'rb') as f:
            s3_client.upload_fileobj(
                f,
                s3_bucket,
                s3_key,
                ExtraArgs={"ContentType": "video/mp4"}
            )
        print(f"Uploaded {mp4_output} to s3://{s3_bucket}/{s3_key}")
    except Exception as e:
        print(f"ERROR: Upload failed: {e}")
        sys.exit(1)
    os.remove(mp4_output)

def launch_gunicorn(flask_port: str) -> None:
    """Launches the Gunicorn server for the Flask app."""
    print("=== 4) Starting Gunicorn (Flask app) ===")
    bind_address = f"0.0.0.0:{flask_port}"
    print(f"Launching Gunicorn on {bind_address}...")
    cmd = [
        "poetry", "run", "gunicorn",
        "refvision.web.flask_app:app",
        "--chdir", "refvision/web",
        "--bind", bind_address,
        "--workers", "2"
    ]
    print(f"Spawning: {' '.join(cmd)}")
    gunicorn_process = subprocess.Popen(cmd)
    time.sleep(3)
    url = f"http://127.0.0.1:{flask_port}"
    print(f"Opening browser at {url}")
    webbrowser.open(url)
    gunicorn_process.wait()
    print("Gunicorn process has exited. Pipeline complete")

def run_pipeline() -> None:
    parser = argparse.ArgumentParser(description="Orchestrate the RefVision pipeline")
    parser.add_argument("--video", default=None, help="Path to raw input video")
    parser.add_argument("--model-path", default=None, help="Path to YOLO model weights")
    parser.add_argument("--avi-output", default=None, help="Where YOLO writes .avi")
    parser.add_argument("--mp4-output", default=None, help="Converted .mp4 file path")
    parser.add_argument("--s3-bucket", default=None, help="S3 bucket for uploading final MP4")
    parser.add_argument("--s3-key", default=None, help="S3 key for final MP4 in S3")
    parser.add_argument("--flask-port", default=None, help="Port for Gunicorn Flask app")
    args = parser.parse_args()

    video = args.video or CFG.VIDEO
    model_path = args.model_path or CFG.MODEL_PATH
    avi_output = args.avi_output or CFG.AVI_OUTPUT
    mp4_output = args.mp4_output or CFG.MP4_OUTPUT
    s3_bucket = args.s3_bucket or CFG.S3_BUCKET
    s3_key = args.s3_key or CFG.S3_KEY
    flask_port = args.flask_port or str(CFG.FLASK_PORT)

    # **NEW STEP: Ingest the normalized video to S3 (simulate live ingestion).**
    from refvision.ingestion.video_ingestor import get_video_ingestor
    ingestor = get_video_ingestor(CFG.TEMP_MP4_FILE, s3_bucket, s3_key)
    ingestor.ingest()

    # Step A: Convert to normalized MP4.
    normalize_video(video, CFG.TEMP_MP4_FILE)

    # Step B: Run YOLO inference.
    run_yolo_inference(CFG.TEMP_MP4_FILE, model_path)

    # Step C: Convert AVI to MP4.
    convert_avi_to_mp4(avi_output, mp4_output)

    # Step D: Upload MP4 to S3.
    upload_video_to_s3(mp4_output, s3_bucket, s3_key)

    # Step E: Launch the Gunicorn (Flask app).
    launch_gunicorn(flask_port)

if __name__ == "__main__":
    run_pipeline()
