# refvision/inference/inference.py
"""
YOLOv11-Based Squat Depth Detection.
This script uses the Ultralytics YOLO model (pose variant) to detect and track lifters
in a video and assess whether they meet squat depth criteria.

Usage example:
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

# Make sure the project root is in the Python path
sys.path.append(
	os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the squat depth decision function (assumed updated to work with our selection logic)
from refvision.find_critical_frame import check_squat_depth_by_turnaround

# --- Logging Setup ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Write logs to logs/yolo_logs.log (create logs/ directory if it doesn't exist)
log_dir = os.path.join(os.path.dirname(__file__), "../../logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "yolo_logs.log")
file_handler = logging.FileHandler(log_file, mode="w")
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Also log to the console
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(file_formatter)
logger.addHandler(stream_handler)

# --- Load Configuration ---
# Assumes the YAML file is located at config/config.yaml in the project root.
config_path = os.path.join(os.path.dirname(__file__), "../../config/config.yaml")
with open(config_path, "r") as f:
	config = yaml.safe_load(f)

# Get lifter selection parameters from the configuration.
lifter_config = config.get("lifter_selector", {})
# expected_center: normalized [x, y] coordinate (0–1) indicating where the lifter is expected to be
expected_center = lifter_config.get("expected_center", [0.5, 0.5])
# roi: optional normalized bounding box [x1, y1, x2, y2]; detections outside this ROI will be ignored
roi = lifter_config.get("roi", None)
# Weighting factors for the scoring function
distance_weight = lifter_config.get("distance_weight", 1.0)
confidence_weight = lifter_config.get("confidence_weight", 1.0)
epsilon = 1e-6  # small constant to prevent division by zero


# --- Lifter Selection Helper Function ---
def select_lifter_index(boxes, orig_w, orig_h):
	"""
    Select the index of the bounding box corresponding to the lifter based on a weighted score.
    The score favors high confidence detections that are close to the expected center (or within an ROI).

    Args:
        boxes: list of detected bounding boxes from the model.
        orig_w: original frame width.
        orig_h: original frame height.

    Returns:
        Index of the selected detection (or None if none qualifies).
    """
	# Compute the expected center in pixel coordinates.
	expected_cx = expected_center[0] * orig_w
	expected_cy = expected_center[1] * orig_h

	best_score = -float("inf")
	lifter_idx = None

	for i, box in enumerate(boxes):
		# Assume box.xyxy is a tensor-like structure with shape [1, 4]
		xyxy = box.xyxy[0]
		x1, y1, x2, y2 = xyxy
		# Compute center of the box.
		cx = (x1 + x2) / 2
		cy = (y1 + y2) / 2
		# Compute Euclidean distance from the expected center.
		dist = math.sqrt((cx - expected_cx) ** 2 + (cy - expected_cy) ** 2)

		# If an ROI is specified (normalized coordinates), skip detections outside of it.
		if roi is not None:
			roi_x1, roi_y1, roi_x2, roi_y2 = roi[0] * orig_w, roi[1] * orig_h, \
											 roi[2] * orig_w, roi[3] * orig_h
			if not (roi_x1 <= cx <= roi_x2 and roi_y1 <= cy <= roi_y2):
				continue

		# Compute the weighted score.
		score = (confidence_weight * box.conf) / (
					distance_weight * (dist + epsilon))
		if score > best_score:
			best_score = score
			lifter_idx = i

	return lifter_idx


# (Note: The lifter selection function above should be integrated into the logic of your
#  critical frame / squat depth evaluation. You can either modify the functions in
#  refvision/find_critical_frame.py to call select_lifter_index() or monkey-patch them here.)

# --- Main Inference Function ---
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

	# Select device (GPU if available, else CPU)
	device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
	logger.info(f"Using device: {device}")

	# Instantiate the YOLO model.
	model = YOLO(args.model_path)
	model.overrides['verbose'] = True

	video_file = args.video
	if not os.path.exists(video_file):
		logger.error(f"Error: Video file {video_file} does not exist.")
		sys.exit(1)
	logger.info(f"Processing video: {video_file}")

	# Run YOLO tracking/pose inference.
	results = model.track(
		source=video_file,
		device=device,
		show=False,
		conf=0.7,
		save=True,
		max_det=1
	)

	# --- Debug Logging: Log details of detections in each frame ---
	logger.debug("========== YOLO Debug Start ==========")
	for frame_i, r in enumerate(results):
		logger.debug(
			f"Frame {frame_i}: #boxes={len(r.boxes)}  #keypoints={len(r.keypoints)}")
		for box_i, box in enumerate(r.boxes):
			box_id = getattr(box, 'id', 'N/A')
			logger.debug(
				f"  Box {box_i}: xyxy={box.xyxy}, conf={box.conf}, id={box_id}")
		for det_i, kpt in enumerate(r.keypoints):
			logger.debug(f"  Keypoints {det_i}: shape={kpt.xy.shape}")
			for kp_idx, point in enumerate(kpt.xy):
				logger.debug(f"    KP {kp_idx}: {point}")
	logger.debug("========== YOLO Debug End ==========")

	# Evaluate squat depth based on the turnaround (bottom) frame.
	# (Assumes check_squat_depth_by_turnaround() has been updated to use the improved lifter selection logic.)
	decision = check_squat_depth_by_turnaround(results)
	logger.info(f"Video: {video_file} => Decision: {decision}")

	# Save the decision to a temporary file (e.g., for later database ingestion).
	tmp_dir = os.path.join(os.path.dirname(__file__), "../../tmp")
	os.makedirs(tmp_dir, exist_ok=True)
	decision_path = os.path.join(tmp_dir, "decision.txt")
	with open(decision_path, "w") as f:
		f.write(decision)


if __name__ == "__main__":
	main()
