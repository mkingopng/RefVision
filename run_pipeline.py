# run_pipeline.py
"""
RefVision Pipeline Runner

This script orchestrates the RefVision pipeline, performing the following steps:
1) Runs YOLO inference (src/main.py) to generate an annotated video (.avi).
2) Converts the .avi file to .mp4 using ffmpeg.
3) Uploads the final .mp4 file to an S3 bucket.
4) Launches Gunicorn to serve `flask_app.py` on the specified port.

Usage Example:
    poetry run python run_pipeline.py \
      --video data/raw_data/chris_kennedy_squat.mp4 \
      --avi-output runs/pose/track2/chris_kennedy_squat.avi \
      --mp4-output runs/pose/track2/chris_kennedy_squat.mp4 \
      --s3-bucket refvision-annotated-videos \
      --s3-key chris_kennedy_squat.mp4
"""
import argparse
import subprocess
import os
import sys
import time
import webbrowser
from typing import List


def run_command(cmd_list: List[str]) -> None:
    """
    Executes a shell command, printing it before execution.
    :param cmd_list: (List[str]) The command and its arguments as a list of strings.
    :return: subprocess.CalledProcessError: If the command fails.
    """
    print(f"Running: {' '.join(cmd_list)}")
    subprocess.check_call(cmd_list)


def main() -> None:
    """
    Main function to orchestrate the RefVision pipeline.
    Steps:
    1) Runs YOLO inference to generate an annotated video.
    2) Converts the output AVI file to MP4 format.
    3) Uploads the MP4 file to S3.
    4) Starts Gunicorn to serve the Flask application.
    """
    parser = argparse.ArgumentParser(
        description="Orchestrate RefVision pipeline."
    )
    parser.add_argument(
        "--video",
        required=True,
        help="Path to raw input video (MP4)."
    )
    parser.add_argument(
        "--model-path",
        default="./model_zoo/yolo11x-pose.pt",
        help="Path to YOLO model weights."
    )
    parser.add_argument(
        "--avi-output",
        default="runs/pose/track2/chris_kennedy_squat.avi",
        help="Path for the YOLO output .avi."
    )
    parser.add_argument(
        "--mp4-output",
        default="runs/pose/track2/chris_kennedy_squat.mp4",
        help="Converted .mp4 file path."
    )
    parser.add_argument(
        "--s3-bucket",
        default="refvision-annotated-videos",
        help="S3 bucket for uploading the final MP4."
    )
    parser.add_argument(
        "--s3-key",
        default="chris_kennedy_squat.mp4",
        help="S3 key (filename) to store the final MP4."
    )
    parser.add_argument(
        "--flask-port",
        default="5000",
        help="Port on which Gunicorn will serve Flask."
    )

    args = parser.parse_args()

    # 1) YOLO inference
    print("=== 1) YOLO Inference ===")
    run_command([
        "poetry", "run", "python", "src/main.py",
        "--video", args.video,
        "--model_path", args.model_path
    ])

    # 2) Convert AVI to MP4
    print("=== 2) Convert AVI to MP4 ===")
    if not os.path.exists(args.avi_output):
        print(f"ERROR: Expected AVI file '{args.avi_output}' not found. Check YOLO output paths.")
        sys.exit(1)

    run_command([
        "ffmpeg", "-y",
        "-i", args.avi_output,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        args.mp4_output
    ])
    os.remove(args.avi_output)

    # 3) Upload MP4 to S3
    print("=== 3) Upload MP4 to S3 ===")
    run_command([
        "aws", "s3", "cp", args.mp4_output,
        f"s3://{args.s3_bucket}/{args.s3_key}",
        "--content-type", "video/mp4"
    ])

    # 4) Start Gunicorn in the background
    print("=== 4) Starting Gunicorn (Flask app) ===")
    bind_address = f"0.0.0.0:{args.flask_port}"
    print("Launching Gunicorn in background...")

    gunicorn_cmd = [
        "poetry", "run", "gunicorn",
        "flask_app:app",
        "--bind", bind_address,
        "--workers", "2"
    ]
    print(f"Spawning: {' '.join(gunicorn_cmd)}")
    gunicorn_process = subprocess.Popen(gunicorn_cmd)

    time.sleep(3)

    url = f"http://127.0.0.1:{args.flask_port}"
    print(f"Opening browser at {url}")
    webbrowser.open(url)

    gunicorn_process.wait()
    print("Gunicorn process has exited. Pipeline complete.")

if __name__ == "__main__":
    main()
