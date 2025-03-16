# refvision/inference/inference.py
"""
Main entrypoint for YOLOv11-Based Squat Depth Detection. This script uses the
Ultralytics YOLO model (pose variant) to detect and track lifters in a video
and assess whether they meet squat depth criteria. The lifter is selected
using parameters from config/config.yaml.

Usage:
    poetry run python refvision/inference/inference.py --video path/to/video.mp4 --model_path ./model_zoo/yolo11x-pose.pt
"""
import os
import sys
import argparse
import yaml
import gc
from typing import Any, List
from refvision.inference.model_loader import load_model
from refvision.analysis.depth_checker import check_squat_depth_by_turnaround
from refvision.utils.logging_setup import setup_logging
from refvision.common.config_base import CONFIG_YAML_PATH
from refvision.utils.timer import measure_time
from refvision.dynamodb.db_handler import store_data  # ✅ Import DynamoDB function

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

logger = setup_logging(
    os.path.join(os.path.dirname(__file__), "../../logs/yolo_logs.log")
)

config_path = CONFIG_YAML_PATH

with open(config_path) as f:
    config = yaml.safe_load(f)


def parse_args() -> argparse.Namespace:
    """
    Parses command line arguments.
    :returns: argparse.Namespace: the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Run YOLO11 pose inference w/ lifter-only skeleton overlay"
    )
    parser.add_argument("--video", type=str, required=True, help="Path to a video file")
    parser.add_argument(
        "--model_path",
        type=str,
        default="./model_zoo/yolo11x-pose.pt",
        help="Path to the YOLO11 pose weights",
    )
    parser.add_argument(
        "--meet_id", type=str, required=True, help="Powerlifting meet ID"
    )
    parser.add_argument("--lifter", type=str, required=True, help="Lifter's name or ID")
    parser.add_argument(
        "--attempt_number", type=int, required=True, help="Attempt number"
    )
    return parser.parse_args()


@measure_time
def run_inference() -> None:
    """
    Main entrypoint for the YOLOv11-based squat depth detection.
    :returns: None
    """
    args = parse_args()
    model, device = load_model(args.model_path)
    video_file = args.video

    if not os.path.exists(video_file):
        logger.error(f"Error: Video file {video_file} does not exist.")
        sys.exit(1)

    logger.info(f"Processing video: {video_file}")

    frame_generator = model.track(
        source=video_file, device=device, show=False, save=True, max_det=1, batch=128
    )

    all_frames = list(frame_generator)
    log_results(all_frames)

    # Evaluate squat depth and save decision
    decision = check_squat_depth_by_turnaround(all_frames)
    logger.info(f"Final decision => {decision}")

    # ✅ Store inference results in DynamoDB instead of writing to JSON
    store_data(args.meet_id, args.lifter, args.attempt_number, decision)
    logger.info(
        f"✅ Inference results stored in DynamoDB for {args.lifter}, attempt {args.attempt_number}"
    )

    gc.collect()


def log_results(results: List[Any]) -> None:
    """
    Logs debug information for each video frame in the results.
    :param results: (List[Any]) Inference results for each frame.
    :returns: None
    """
    logger.debug("========== YOLO Debug Start ==========")
    for frame_i, r in enumerate(results):
        logger.debug(
            f"Frame {frame_i}: #boxes={len(r.boxes)}  #keypoints={len(r.keypoints)}"
        )
        for box_i, box in enumerate(r.boxes):
            box_id = getattr(box, "stack_id", "N/A")
            logger.debug(
                f"Box {box_i}: xyxy={box.xyxy}, conf={box.conf}, stack_id={box_id}"
            )
        for det_i, kpt in enumerate(r.keypoints):
            logger.debug(f"  Keypoints {det_i}: shape={kpt.xy.shape}")
    logger.debug("========== YOLO Debug End ==========")


if __name__ == "__main__":
    run_inference()
