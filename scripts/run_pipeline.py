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
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.config import CFG


def run_command(cmd_list: List[str]) -> None:
    """
    Runs a shell command, printing it first.
    Raises CalledProcessError if the command fails.
    :param cmd_list: List of command arguments.
    :return: None
    """
    print(f"Running: {' '.join(cmd_list)}")
    subprocess.check_call(cmd_list)


def main() -> None:
    """
    Main entrypoint for the RefVision pipeline
    :return: None
    """
    parser = argparse.ArgumentParser(
        description="Orchestrate the RefVision pipeline"
    )

    parser.add_argument(
        "--video",
        default=None,
        help="Path to raw input video (MOV/MP4/etc)"
    )

    parser.add_argument(
        "--model-path",
        default=None,
        help="Path to YOLO model weights"
    )

    parser.add_argument(
        "--avi-output",
        default=None,
        help="Where YOLO writes .avi"
    )

    parser.add_argument(
        "--mp4-output",
        default=None,
        help="Converted .mp4 file path"
    )

    parser.add_argument(
        "--s3-bucket",
        default=None,
        help="S3 bucket for uploading final MP4"
    )

    parser.add_argument(
        "--s3-key",
        default=None,
        help="S3 key for final MP4 in S3"
    )

    parser.add_argument(
        "--flask-port",
        default=None,
        help="Port for Gunicorn Flask app"
    )

    args = parser.parse_args()

    # merge CLI with config
    video = args.video or CFG.VIDEO
    model_path = args.model_path or CFG.MODEL_PATH
    avi_output = args.avi_output or CFG.AVI_OUTPUT
    mp4_output = args.mp4_output or CFG.MP4_OUTPUT
    s3_bucket = args.s3_bucket or CFG.S3_BUCKET
    s3_key = args.s3_key or CFG.S3_KEY
    flask_port = args.flask_port or str(CFG.FLASK_PORT)

    # ensure root project directory is in Python path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    # A) convert any input to a normalised MP4
    print("=== Pre-step: Normalize input to MP4 ===")
    normalized_input = CFG.TEMP_MP4_FILE
    pre_ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-map_metadata",
        "-1",
        normalized_input
    ]
    run_command(pre_ffmpeg_cmd)

    # 1) inference
    print("=== 1) YOLO Inference ===")
    run_command([
        "poetry",
        "run",
        "python",
        "-m",
        "refvision.inference.inference",
        "--video",
        normalized_input,
        "--model_path",
        model_path
    ])

    # 2) convert YOLO's .avi output to .mp4
    print("=== 2) Convert AVI to MP4 ===")
    if not os.path.exists(avi_output):
        print(f"ERROR: Expected AVI file '{avi_output}' not found")
        sys.exit(1)

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        avi_output,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        mp4_output
    ]
    run_command(ffmpeg_cmd)
    os.remove(avi_output)

    # 3) upload MP4 to S3
    print("=== 3) Upload MP4 to S3 ===")
    run_command([
        "aws",
        "s3",
        "cp",
        mp4_output,
        f"s3://{s3_bucket}/{s3_key}",
        "--content-type",
        "video/mp4"
    ])
    os.remove(f"{CFG.TEMP_MP4_FILE}")
    os.remove(f"runs/pose/track/{CFG.VIDEO_NAME}.mp4")

    # 4) start Gunicorn in background
    print("=== 4) Starting Gunicorn (Flask app) ===")
    bind_address = f"0.0.0.0:{flask_port}"
    print(f"Launching Gunicorn on {bind_address}...")

    gunicorn_cmd = [
        "poetry",
        "run",
        "gunicorn",
        "refvision.web.flask_app:app",
        "--chdir",
        "refvision/web",
        "--bind",
        bind_address,
        "--workers",
        "2"
    ]
    print(f"Spawning: {' '.join(gunicorn_cmd)}")
    gunicorn_process = subprocess.Popen(gunicorn_cmd)

    time.sleep(3)

    url = f"http://127.0.0.1:{flask_port}"
    print(f"Opening browser at {url}")
    webbrowser.open(url)

    gunicorn_process.wait()
    print("Gunicorn process has exited. Pipeline complete")


if __name__ == "__main__":
    main()
