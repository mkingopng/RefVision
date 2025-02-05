# run_pipeline.py
"""
Usage (example):
    poetry run python run_pipeline.py \
      --video data/raw_data/chris_kennedy_squat.mp4 \
      --avi-output runs/pose/track2/chris_kennedy_squat.avi \
      --mp4-output runs/pose/track2/chris_kennedy_squat.mp4 \
      --s3-bucket refvision-annotated-videos \
      --s3-key chris_kennedy_squat.mp4

What it does:
1) Runs YOLO inference (src/main.py), producing an .avi.
2) Converts .avi to .mp4 using ffmpeg.
3) Uploads the .mp4 to S3.
4) Launches Gunicorn to serve flask_app.py at 0.0.0.0:5000.
"""

import argparse
import subprocess
import os
import sys
import time
import webbrowser

def run_command(cmd_list):
    """Helper function to print and run shell commands with error checking."""
    print(f"Running: {' '.join(cmd_list)}")
    subprocess.check_call(cmd_list)

def main():
    parser = argparse.ArgumentParser(description="Orchestrate RefVision pipeline.")
    parser.add_argument("--video", required=True, help="Path to raw input video (MP4).")
    parser.add_argument("--model-path", default="./model_zoo/yolo11x-pose.pt",
                        help="Path to YOLO model weights.")
    parser.add_argument("--avi-output", default="runs/pose/track2/chris_kennedy_squat.avi",
                        help="Path for the YOLO output .avi.")
    parser.add_argument("--mp4-output", default="runs/pose/track2/chris_kennedy_squat.mp4",
                        help="Converted .mp4 file path.")
    parser.add_argument("--s3-bucket", default="refvision-annotated-videos",
                        help="S3 bucket for uploading the final MP4.")
    parser.add_argument("--s3-key", default="chris_kennedy_squat.mp4",
                        help="S3 key (filename) to store the final MP4.")
    parser.add_argument("--flask-port", default="5000",
                        help="Port on which Gunicorn will serve Flask.")
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
    os.remove(args.avi_output)  # optional: remove the .avi after conversion

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

    # Instead of check_call (which blocks), use Popen
    gunicorn_cmd = [
        "poetry", "run", "gunicorn",
        "flask_app:app",
        "--bind", bind_address,
        "--workers", "2"
    ]
    print(f"Spawning: {' '.join(gunicorn_cmd)}")
    gunicorn_process = subprocess.Popen(gunicorn_cmd)

    # OPTIONAL: Wait a couple seconds for Gunicorn to initialize
    time.sleep(3)

    # Open the browser to Flask homepage
    url = f"http://127.0.0.1:{args.flask_port}"
    print(f"Opening browser at {url}")
    webbrowser.open(url)

    # Wait for Gunicorn to exit (so the script doesn't terminate immediately)
    gunicorn_process.wait()
    print("Gunicorn process has exited. Pipeline complete.")

if __name__ == "__main__":
    main()
