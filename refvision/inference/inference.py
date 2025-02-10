# refvision/inference/inference.py
"""
YOLOv11-Based Squat Depth Detection.
This script uses the Ultralytics YOLO model (pose variant) to detect and track lifters
in a video and assess whether they meet squat depth criteria. The lifter is selected
using parameters from config/config.yaml.
Usage:
    poetry run python refvision/inference/inference.py --video path/to/video.mp4 --model_path ./model_zoo/yolo11x-pose.pt
"""
import os
import sys
import argparse
import logging
import yaml
import math
from ultralytics import YOLO
import torch
import cv2
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from refvision.find_critical_frame import check_squat_depth_by_turnaround, select_lifter_index

# logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
log_dir = os.path.join(os.path.dirname(__file__), "../../logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "yolo_logs.log")
file_handler = logging.FileHandler(log_file, mode="w")
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(file_formatter)
logger.addHandler(stream_handler)

config_path = os.path.join(os.path.dirname(__file__), "../../config/config.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)


def main() -> None:
    """
    Main entrypoint for the YOLOv11-based squat depth detection.
    :return: None
    """
    parser = argparse.ArgumentParser(
        description="Run YOLO11 pose inference with lifter-only skeleton overlay."
    )

    parser.add_argument(
        "--video",
        type=str,
        required=True,
        help="Path to a video file"
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

    model = YOLO(args.model_path)
    model.overrides['verbose'] = True

    video_file = args.video
    if not os.path.exists(video_file):
        logger.error(f"Error: Video file {video_file} does not exist.")
        sys.exit(1)
    logger.info(f"Processing video: {video_file}")

    results = model.track(
        source=video_file,
        device=device,
        show=False,
        # conf=0.7,
        save=True,
        max_det=1
    )

    # debug logging
    logger.debug("========== YOLO Debug Start ==========")
    for frame_i, r in enumerate(results):
        logger.debug(f"Frame {frame_i}: #boxes={len(r.boxes)}  #keypoints={len(r.keypoints)}")
        for box_i, box in enumerate(r.boxes):
            box_id = getattr(box, 'id', 'N/A')
            logger.debug(f"Box {box_i}: xyxy={box.xyxy}, conf={box.conf}, id={box_id}")
        for det_i, kpt in enumerate(r.keypoints):
            logger.debug(f"  Keypoints {det_i}: shape={kpt.xy.shape}")
    logger.debug("========== YOLO Debug End ==========")

    excluded_ids = config.get("lifter_selector", {}).get("excluded_ids", [])

    # Annotate Video
    cap = cv2.VideoCapture(video_file)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_path = os.path.join("tmp", "annotated_output.mp4")
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx < len(results):
            frame_result = results[frame_idx]
            # check if we have detections in the frame
            if frame_result.keypoints and frame_result.boxes:
                # use your lifter selection function to choose which box to annotate.
                lifter_idx = select_lifter_index(frame_result.boxes, width, height)
                # additional check: if the selected id is in the exclusion list, skip drawing.
                if lifter_idx is not None:
                    box = frame_result.boxes[lifter_idx]
                    # ensure that the box has an 'id' attribute
                    box_id = getattr(box, 'id', None)
                    if box_id is not None and box_id in excluded_ids:
                        logger.debug(f"Skipping skeleton overlay for detection with id {box_id}.")
                    else:
                        # process the keypoints and draw the skeleton
                        kpts = frame_result.keypoints[lifter_idx]
                        if len(kpts.xy.shape) == 3 and kpts.xy.shape[0] == 1:
                            kpts_xy = kpts.xy.squeeze(0)
                        else:
                            kpts_xy = kpts.xy
                        keypoints = np.array(kpts_xy.cpu() if hasattr(kpts_xy, "cpu") else kpts_xy)
                        for x, y in keypoints:
                            cv2.circle(frame, (int(x), int(y)), 4, (0, 255, 0), -1)

        writer.write(frame)
        frame_idx += 1

    cap.release()
    writer.release()
    logger.info(f"Annotated video saved to {out_path}")

    # evaluate Squat Depth
    decision = check_squat_depth_by_turnaround(results)
    logger.info(f"Video: {video_file} => Decision: {decision}")

    tmp_dir = os.path.join(os.path.dirname(__file__), "../../tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    decision_path = os.path.join(tmp_dir, "decision.txt")
    with open(decision_path, "w") as f:
        f.write(decision)

if __name__ == "__main__":
    main()
