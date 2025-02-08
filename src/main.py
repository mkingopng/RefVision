# src/main.py
"""
YOLOv11-Based Squat Depth Detection. This script uses the Ultralytics YOLOv11
model to detect and track lifters in a video and assess whether they meet squat
depth criteria.

Usage Example:
    python src/main.py --video path/to/video.mp4 --model_path path/to/yolo11-model.pt

Arguments:
    --video Path to the input video file.
    --model_path Path to the YOLOv11 pose estimation model weights
"""
import os
import sys
import argparse
from ultralytics import YOLO
import torch
from find_critical_frame import check_squat_depth_by_turnaround


def main() -> None:
    """
    Main function to process a video file using YOLOv11 for pose estimation and
    squat depth analysis.
    Steps:
    1. Load the YOLO model.
    2. Validate input video path.
    3. Perform pose tracking and inference.
    4. Apply squat depth evaluation logic.
    5. Output the decision.
    """
    parser = argparse.ArgumentParser(
        description="Run YOLO11 pose inference with pass/fail logic"
    )

    parser.add_argument(
        "--video",
        type=str,
        required=True,
        help="Path to a single video file"
    )

    parser.add_argument(
        "--model_path",
        type=str,
        default="./model_zoo/yolo11x-pose.pt",
        help="Path to the YOLO11 pose weights"
    )

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

    decision = check_squat_depth_by_turnaround(results)
    print(f"Video: {video_file} => Decision: {decision}\n")

    with open("decision.txt", "w") as f:
        f.write(decision)

if __name__ == "__main__":
    main()
