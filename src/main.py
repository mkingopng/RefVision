# src/main.py
"""
This script demonstrates how to use the Ultralytics YOLOv5 model to detect and
track people in videos.
"""
import os
import sys
import argparse
from ultralytics import YOLO
import torch
from check_squat_depth import check_squat_depth


def main():
    """
    Main function to process videos and determine squat depth.
    :return:
    """
    parser = argparse.ArgumentParser(description="Run local YOLO11 pose inference on CPU with pass/fail logic")
    parser.add_argument("--video", type=str, required=True, help="Path to a single video file")
    parser.add_argument("--model_path", type=str, default="./model_zoo/yolo11x-pose.pt", help="Path to the YOLO11 pose weights")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    model = YOLO(args.model_path)
    video_file = args.video
    if not os.path.exists(video_file):
        print(f"Error: Video file {video_file} does not exist.")
        sys.exit(1)

    print(f"Processing video: {video_file}")

    results = model.track(
        source=video_file,
        device=device,
        show=False,
        conf=0.8,
        save=True,
        max_det=5
    )

    # simple pass/fail check
    decision = check_squat_depth(results)
    print(f"Video: {video_file} => Decision: {decision}\n")

if __name__ == "__main__":
    main()
