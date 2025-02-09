# src/main.py
"""
YOLOv11-Based Squat Depth Detection.
This script uses the Ultralytics YOLO model (pose variant) to detect and track lifters
in a video and assess whether they meet squat depth criteria.

Usage example:
    poetry run python src/main.py --video path/to/video.mp4 --model_path ./model_zoo/yolo11x-pose.pt
"""
import os
import sys
import argparse
import logging
import sys
from ultralytics import YOLO
import torch
from find_critical_frame import check_squat_depth_by_turnaround

# --- Explicit Logging Setup ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a file handler that writes debug logs to "yolo_logs.log"
file_handler = logging.FileHandler("yolo_logs.log", mode="w")
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Optionally add a stream handler (console)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(file_formatter)
logger.addHandler(stream_handler)
# --- End Logging Setup ---

def main() -> None:
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
    logger.info(f"Using device: {device}")

    # Instantiate the model
    model = YOLO(args.model_path)
    # Uncomment the following line if your YOLO implementation supports verbosity:
    # model.overrides['verbose'] = True

    video_file = args.video
    if not os.path.exists(video_file):
        logger.error(f"Error: Video file {video_file} does not exist.")
        sys.exit(1)

    logger.info(f"Processing video: {video_file}")

    # Run YOLO tracking/pose inference
    results = model.track(
        source=video_file,
        device=device,
        show=False,
        conf=0.8,
        save=True,
        max_det=5
    )

    # --- Debugging: Log YOLO result details ---
    logger.debug("========== YOLO Debug Start ==========")
    for frame_i, r in enumerate(results):
        logger.debug(f"Frame {frame_i}: #boxes={len(r.boxes)}  #keypoints={len(r.keypoints)}")
        for box_i, box in enumerate(r.boxes):
            box_id = getattr(box, 'id', 'N/A')
            logger.debug(f"  Box {box_i}: xyxy={box.xyxy}, conf={box.conf}, id={box_id}")
        for det_i, kpt in enumerate(r.keypoints):
            logger.debug(f"  Keypoints {det_i}: shape={kpt.xy.shape}")
            for kp_idx, point in enumerate(kpt.xy):
                logger.debug(f"    KP {kp_idx}: {point}")
    logger.debug("========== YOLO Debug End ==========")
    # --- End Debugging ---

    # Evaluate squat depth based on the turnaround frame.
    decision = check_squat_depth_by_turnaround(results)
    logger.info(f"Video: {video_file} => Decision: {decision}")

    # Save the decision to a text file.
    with open("decision.txt", "w") as f:
        f.write(decision)

if __name__ == "__main__":
    main()
