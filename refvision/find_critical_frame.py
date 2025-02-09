"""
Module for identifying the turnaround (bottom) frame in a squat video
and checking squat depth at that frame.
"""

import logging
from typing import List, Optional
from config.config import CFG

# --- Logging Setup ---
# Logs will be written to logs/debug.log and also streamed to console.
logging.basicConfig(
	level=logging.DEBUG,
	format="%(asctime)s - %(levelname)s - %(message)s",
	handlers=[
		logging.FileHandler("logs/debug.log", mode="w"),
		logging.StreamHandler()
	]
)
logger = logging.getLogger(__name__)

# Keypoint indices – adjust these if your keypoint order is different
LEFT_HIP_IDX = 11
RIGHT_HIP_IDX = 12
LEFT_KNEE_IDX = 13
RIGHT_KNEE_IDX = 14


def find_turnaround_frame(results: List, smoothing_window: int = 1) -> \
Optional[int]:
	"""
    Identifies the frame where the lifter reaches their lowest hip position
    (i.e. the highest y value) in the video. This approach uses the global maximum
    among valid (smoothed) hip positions.

    Args:
        results: List of frame results from YOLO inference.
        smoothing_window: Size of the moving average window for hip smoothing.

    Returns:
        The index of the turnaround frame, or None if no valid frame is found.
    """
	logger.debug("=== find_turnaround_frame called ===")
	hip_positions = []

	# Process each frame in the results
	for f_idx, frame_result in enumerate(results):
		# Skip frames without keypoints or bounding boxes.
		if not frame_result.keypoints or not frame_result.boxes:
			logger.debug(
				f"Frame {f_idx}: No keypoints or boxes. Marking as None.")
			hip_positions.append(None)
			continue

		# Use the original image shape if available; otherwise default to 640x640.
		if hasattr(frame_result, 'orig_shape') and frame_result.orig_shape:
			orig_h, orig_w = frame_result.orig_shape
		else:
			orig_h, orig_w = 640, 640

		center_x_img = orig_w / 2
		center_y_img = orig_h / 2

		# --- Lifter Selection ---
		lifter_idx = None

		# First, try to select the detection with a matching LIFTER_ID from the configuration.
		if CFG.LIFTER_ID is not None:
			for i, box in enumerate(frame_result.boxes):
				if hasattr(box, 'id') and box.id == CFG.LIFTER_ID:
					lifter_idx = i
					logger.debug(
						f"Frame {f_idx}: Found box with LIFTER_ID={CFG.LIFTER_ID} at index {i}.")
					break

		# If no detection matches the LIFTER_ID, select the detection closest to the image center.
		if lifter_idx is None:
			min_dist_sq = float('inf')
			for i, box in enumerate(frame_result.boxes):
				# Assume box.xyxy is a tensor or list with shape [1, 4]: [x1, y1, x2, y2]
				xyxy = box.xyxy[0]
				x1, y1, x2, y2 = xyxy
				cx = (x1 + x2) / 2
				cy = (y1 + y2) / 2
				dist_sq = (cx - center_x_img) ** 2 + (cy - center_y_img) ** 2
				if dist_sq < min_dist_sq:
					min_dist_sq = dist_sq
					lifter_idx = i
			logger.debug(
				f"Frame {f_idx}: No matching LIFTER_ID found. Using box closest to center (index {lifter_idx}).")
		# --- End Lifter Selection ---

		# Retrieve keypoints for the selected detection.
		kpts = frame_result.keypoints[lifter_idx]
		# Remove an extra singleton dimension if present.
		if len(kpts.xy.shape) == 3 and kpts.xy.shape[0] == 1:
			kpts_xy = kpts.xy.squeeze(0)
		else:
			kpts_xy = kpts.xy

		# Ensure that we have enough keypoints to obtain hips and knees.
		if kpts_xy.shape[0] <= RIGHT_KNEE_IDX:
			logger.debug(
				f"Frame {f_idx}: Not enough keypoints (<= {RIGHT_KNEE_IDX}). Marking as None.")
			hip_positions.append(None)
			continue

		left_hip_y = kpts_xy[LEFT_HIP_IDX, 1].item()
		right_hip_y = kpts_xy[RIGHT_HIP_IDX, 1].item()
		avg_hip_y = (left_hip_y + right_hip_y) / 2.0

		logger.debug(
			f"Frame {f_idx}: lifter_idx={lifter_idx}, left_hip_y={left_hip_y}, "
			f"right_hip_y={right_hip_y}, avg_hip_y={avg_hip_y}"
		)
		hip_positions.append(avg_hip_y)

	# 2. Smooth the hip positions (ignoring None values).
	smoothed_hips = smooth_series(hip_positions, window_size=smoothing_window)
	logger.debug(f"Hip positions (raw): {hip_positions}")
	logger.debug(f"Hip positions (smoothed): {smoothed_hips}")

	# 3. Choose the frame with the global maximum hip y value (i.e. the lowest physical hip position).
	valid_idxs = [i for i, v in enumerate(smoothed_hips) if v is not None]
	logger.debug(f"Valid indexes: {valid_idxs}")
	if not valid_idxs:
		logger.info(
			"No valid frames to determine a turnaround. Returning None.")
		return None

	best_idx = max(valid_idxs, key=lambda i: smoothed_hips[i])
	logger.info(f"Turnaround frame index (global max) => {best_idx}")
	return best_idx


def smooth_series(values: List[Optional[float]], window_size: int = 1) -> List[
	Optional[float]]:
	"""
    Smooths a series of values using a simple moving average (ignoring None values).

    Args:
        values: A list of values (or None) to smooth.
        window_size: The size of the moving average window.

    Returns:
        A list of smoothed values.
    """
	logger = logging.getLogger(__name__)
	if window_size < 2:
		return values

	smoothed = [None] * len(values)
	half_w = window_size // 2

	for i in range(len(values)):
		if values[i] is None:
			smoothed[i] = None
			continue

		local_vals = [values[j] for j in range(i - half_w, i + half_w + 1)
					  if 0 <= j < len(values) and values[j] is not None]
		smoothed[i] = sum(local_vals) / len(local_vals) if local_vals else None

	return smoothed


def check_squat_depth_at_frame(
		results: List, frame_idx: int, threshold: float = -30.0
		) -> Optional[str]:
	"""
    Evaluates squat depth at a specific frame by comparing the average hip and knee positions.

    Args:
        results: List of frame results from YOLO inference.
        frame_idx: Index of the frame to evaluate.
        threshold: Depth threshold for a successful squat.

    Returns:
        "PASS" if the squat meets the threshold, "FAIL" otherwise.
    """
	logger = logging.getLogger(__name__)
	logger.debug(
		f"=== check_squat_depth_at_frame(frame_idx={frame_idx}, threshold={threshold}) ===")

	if frame_idx is None or frame_idx < 0 or frame_idx >= len(results):
		logger.debug("Invalid frame_idx. Returning None.")
		return None

	frame_result = results[frame_idx]
	if not frame_result.keypoints or not frame_result.boxes:
		logger.debug("No keypoints or boxes in chosen frame. Returning None.")
		return None

	if hasattr(frame_result, 'orig_shape') and frame_result.orig_shape:
		orig_h, orig_w = frame_result.orig_shape
	else:
		orig_h, orig_w = 640, 640

	center_x_img = orig_w / 2
	center_y_img = orig_h / 2

	# --- Lifter Selection for this frame ---
	lifter_idx = None
	if CFG.LIFTER_ID is not None:
		for i, box in enumerate(frame_result.boxes):
			if hasattr(box, 'id') and box.id == CFG.LIFTER_ID:
				lifter_idx = i
				logger.debug(
					f"Frame {frame_idx}: Found box with LIFTER_ID={CFG.LIFTER_ID} at index {i}.")
				break

	if lifter_idx is None:
		# Fallback: choose the box closest to the center.
		min_dist_sq = float('inf')
		for i, box in enumerate(frame_result.boxes):
			xyxy = box.xyxy[0]
			x1, y1, x2, y2 = xyxy
			cx = (x1 + x2) / 2
			cy = (y1 + y2) / 2
			dist_sq = (cx - center_x_img) ** 2 + (cy - center_y_img) ** 2
			if dist_sq < min_dist_sq:
				min_dist_sq = dist_sq
				lifter_idx = i
		logger.debug(
			f"Frame {frame_idx}: No matching LIFTER_ID found. Using box closest to center (index {lifter_idx}).")
	# --- End lifter selection ---

	kpts = frame_result.keypoints[lifter_idx]
	if len(kpts.xy.shape) == 3 and kpts.xy.shape[0] == 1:
		kpts_xy = kpts.xy.squeeze(0)
	else:
		kpts_xy = kpts.xy

	if kpts_xy.shape[0] <= RIGHT_KNEE_IDX:
		logger.debug("Not enough keypoints to retrieve hips/knees.")
		return None

	left_hip_y = kpts_xy[LEFT_HIP_IDX, 1].item()
	right_hip_y = kpts_xy[RIGHT_HIP_IDX, 1].item()
	left_knee_y = kpts_xy[LEFT_KNEE_IDX, 1].item()
	right_knee_y = kpts_xy[RIGHT_KNEE_IDX, 1].item()

	avg_hip_y = (left_hip_y + right_hip_y) / 2.0
	avg_knee_y = (left_knee_y + right_knee_y) / 2.0
	best_delta = avg_hip_y - avg_knee_y

	logger.debug(
		f"Frame {frame_idx}: left_hip_y={left_hip_y}, right_hip_y={right_hip_y}, "
		f"left_knee_y={left_knee_y}, right_knee_y={right_knee_y}, "
		f"avg_hip_y={avg_hip_y}, avg_knee_y={avg_knee_y}, "
		f"best_delta={best_delta}, threshold={threshold}"
	)

	if best_delta > threshold:
		logger.debug("Frame => PASS")
		return "PASS"
	else:
		logger.debug("Frame => FAIL")
		return "FAIL"


def check_squat_depth_by_turnaround(
		results: List, threshold: float = 0.0
		) -> str:
	"""
    Uses find_turnaround_frame to select the squat’s bottom frame and then
    checks the squat depth on that frame.

    Args:
        results: List of frame results from YOLO inference.
        threshold: Depth threshold for a successful squat.

    Returns:
        "PASS" if the squat meets the threshold, "FAIL" otherwise.
    """
	logger = logging.getLogger(__name__)
	logger.debug(
		f"=== check_squat_depth_by_turnaround(threshold={threshold}) ===")

	turnaround_idx = find_turnaround_frame(results)
	logger.debug(f"Turnaround frame => {turnaround_idx}")

	if turnaround_idx is None:
		logger.info("No valid turnaround frame found, returning FAIL.")
		return "FAIL"

	decision = check_squat_depth_at_frame(results, turnaround_idx, threshold)
	logger.debug(f"Decision from turnaround frame => {decision}")
	final = decision if decision == "PASS" else "FAIL"
	logger.info(f"check_squat_depth_by_turnaround => {final}")
	return final
