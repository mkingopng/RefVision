# refvision/inference/local_inference.py
"""
Main entrypoint for YOLOv11-Based Squat Depth Detection. This script uses the
Ultralytics YOLO model (pose variant) to detect and track lifters in a video
and assess whether they meet squat depth criteria. The lifter is selected
using parameters from config/config.yaml.
"""

import os
import sys
import yaml
import gc
import argparse
from refvision.inference.model_loader import load_model
from refvision.analysis.depth_checker import check_squat_depth_by_turnaround
from refvision.utils.logging_setup import setup_logging
from refvision.common.config import CONFIG_YAML_PATH, get_config
from refvision.utils.timer import measure_time
from refvision.dynamo_db.dynamodb_helpers import update_item, decimalize

cfg = get_config()
logger = setup_logging(
    os.path.join(os.path.dirname(__file__), "../../logs/yolo_logs.log")
)

config_path = CONFIG_YAML_PATH
with open(config_path) as f:
    config = yaml.safe_load(f)


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Run YOLO pose inference")
    parser.add_argument("--video", required=True, help="Path to .mp4/.mov video")
    parser.add_argument("--model_path", default="./model_zoo/yolo11x-pose.pt")
    parser.add_argument("--athlete_id", required=True, help="PK in DynamoDB")
    parser.add_argument("--record_id", required=True, help="SK in DynamoDB")
    return parser.parse_args()


@measure_time
def run_inference(
    video_file: str, model_path: str, meet_name: str, record_id: str
) -> None:
    """
    Actually runs YOLO pose inference and updates DynamoDB with the final decision.
    :param video_file: Path to the input video file.
    :param model_path: Path to the YOLO model file.
    :param meet_name: PK in DynamoDB.
    :param record_id: SK in DynamoDB.
    :return: None
    """
    if not os.path.exists(video_file):
        logger.error(f"Error: Video file {video_file} does not exist.")
        sys.exit(1)

    # 1) load YOLO
    model, device = load_model(model_path)
    logger.info(f"Processing video: {video_file}")

    # 2) pose tracking => writes .avi in runs/pose/track
    frame_generator = model.track(
        source=video_file,
        device=device,
        show=False,
        save=True,
        project=cfg["OUTPUT_DIR"],
        exist_ok=True,
        max_det=1,
        batch=128,
    )
    all_frames = list(frame_generator)

    # 3) evaluate squat depth
    decision = check_squat_depth_by_turnaround(all_frames)
    logger.info(f"Final decision => {decision}")

    # 4) update existing DynamoDB record
    decision = decimalize(decision)

    update_item(
        meet_id=meet_name,
        record_id=record_id,
        updates={"InferenceResult": decision, "Status": "COMPLETED"},
    )
    logger.info(f"DynamoDB updated => meet_name={meet_name}, record_id={record_id}")
    gc.collect()


def main():
    """
    Main function to parse arguments and run inference.
    :return: None
    """
    args = parse_args()
    run_inference(args.video, args.model_path, args.athlete_id, args.record_id)


if __name__ == "__main__":
    main()
