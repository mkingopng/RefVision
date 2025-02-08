# run_pipeline.py
"""
RefVision Pipeline Runner

Steps:
A) Convert any raw input (MOV, etc.) to a normalized MP4 (with no orientation metadata).
1) YOLO inference -> produces an annotated .avi
2) Convert .avi -> .mp4
3) Upload .mp4 to S3
4) Launch Gunicorn to serve Flask on specified port.

Override defaults with CLI arguments if needed.

Example usage:
  poetry run python run_pipeline.py
Or:
  poetry run python run_pipeline.py --video data/raw_data/lifter.mp4 --flask-port 6000
"""
import argparse
import subprocess
import os
import sys
import time
import webbrowser
from typing import List

from config import CFG


def run_command(cmd_list: List[str]) -> None:
    """
    Runs a shell command, printing it first.
    Raises CalledProcessError if the command fails.
    """
    print(f"Running: {' '.join(cmd_list)}")
    subprocess.check_call(cmd_list)


def main() -> None:
    parser = argparse.ArgumentParser(description="Orchestrate the RefVision pipeline.")
    parser.add_argument("--video", default=None, help="Path to raw input video (MOV/MP4/etc.).")
    parser.add_argument("--model-path", default=None, help="Path to YOLO model weights.")
    parser.add_argument("--avi-output", default=None, help="Where YOLO writes .avi.")
    parser.add_argument("--mp4-output", default=None, help="Converted .mp4 file path.")
    parser.add_argument("--s3-bucket", default=None, help="S3 bucket for uploading final MP4.")
    parser.add_argument("--s3-key", default=None, help="S3 key for final MP4 in S3.")
    parser.add_argument("--flask-port", default=None, help="Port for Gunicorn Flask app.")
    args = parser.parse_args()

    # Merge CLI with config
    video       = args.video       or CFG.video
    model_path  = args.model_path  or CFG.model_path
    avi_output  = args.avi_output  or CFG.avi_output
    mp4_output  = args.mp4_output  or CFG.mp4_output
    s3_bucket   = args.s3_bucket   or CFG.s3_bucket
    s3_key      = args.s3_key      or CFG.s3_key
    flask_port  = args.flask_port  or str(CFG.flask_port)

    # A) Convert any input to a normalized MP4 (physically upright frames)
    # Using ffmpeg auto-rotation. Also stripping metadata to remove orientation tags.
    print("=== Pre-step: Normalize input to MP4 ===")
    normalized_input = CFG.mp4_file
    pre_ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", video,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        # Strip metadata so we remove any rotation tags
        "-map_metadata", "-1",
        normalized_input
    ]
    run_command(pre_ffmpeg_cmd)

    # 1) YOLO Inference (using the normalized MP4)
    print("=== 1) YOLO Inference ===")
    run_command([
        "poetry", "run", "python", "src/main.py",
        "--video", normalized_input,
        "--model_path", model_path
    ])

    # 2) Convert YOLO's .avi output to .mp4
    print("=== 2) Convert AVI to MP4 ===")
    if not os.path.exists(avi_output):
        print(f"ERROR: Expected AVI file '{avi_output}' not found. Check YOLO output path.")
        sys.exit(1)

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", avi_output,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        mp4_output
    ]
    run_command(ffmpeg_cmd)
    os.remove(avi_output)

    # 3) Upload MP4 to S3
    print("=== 3) Upload MP4 to S3 ===")
    run_command([
        "aws", "s3", "cp", mp4_output,
        f"s3://{s3_bucket}/{s3_key}",
        "--content-type", "video/mp4"
    ])

    # 4) Start Gunicorn in the background
    print("=== 4) Starting Gunicorn (Flask app) ===")
    bind_address = f"0.0.0.0:{flask_port}"
    print(f"Launching Gunicorn on {bind_address}...")

    gunicorn_cmd = [
        "poetry", "run", "gunicorn",
        "flask_app:app",
        "--bind", bind_address,
        "--workers", "2"
    ]
    print(f"Spawning: {' '.join(gunicorn_cmd)}")
    gunicorn_process = subprocess.Popen(gunicorn_cmd)

    time.sleep(3)

    url = f"http://127.0.0.1:{flask_port}"
    print(f"Opening browser at {url}")
    webbrowser.open(url)

    gunicorn_process.wait()
    print("Gunicorn process has exited. Pipeline complete.")


if __name__ == "__main__":
    main()
