# src/find_critical_frame.py
"""
Module for identifying the turnaround (bottom) frame in a squat video
and checking squat depth at that frame.

This module provides:
- `find_turnaround_frame`: Finds the frame where the lifter reaches their lowest hip position.
- `smooth_series`: Applies optional smoothing to hip position data.
- `check_squat_depth_at_frame`: Checks squat depth for a specific frame.
- `check_squat_depth_by_turnaround`: Uses `find_turnaround_frame` to check depth at the turnaround point.
"""
import logging
import numpy as np
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to INFO if DEBUG is too verbose
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("debug.log", mode="w"),  # Save logs to a file
        logging.StreamHandler()  # Print logs to console as well
    ]
)

logger = logging.getLogger(__name__)

LEFT_HIP_IDX = 11
RIGHT_HIP_IDX = 12
LEFT_KNEE_IDX = 13
RIGHT_KNEE_IDX = 14

def find_turnaround_frame(
    results: List,
    smoothing_window: int = 1
) -> Optional[int]:
    """
    Identifies the frame where the lifter reaches the lowest hip position before ascending.
    Process:
      1. Extracts the average hip Y position for each frame (ignoring invalid frames).
      2. (Optional) Applies smoothing to reduce noise.
      3. Finds the local maximum Y position (the turnaround point).
    """
    logger.debug("=== find_turnaround_frame called ===")
    hip_positions = []

    # 1. Build a list of average hip Y per frame
    for f_idx, frame_result in enumerate(results):
        # Basic checks
        if not frame_result.keypoints or not frame_result.boxes:
            logger.debug(f"Frame {f_idx}: No keypoints or boxes. Marking as None.")
            hip_positions.append(None)
            continue

        # Identify lifter's bounding box
        if hasattr(frame_result, 'orig_shape') and frame_result.orig_shape:
            orig_h, orig_w = frame_result.orig_shape
        else:
            orig_h, orig_w = 640, 640

        center_x_img = orig_w / 2
        center_y_img = orig_h / 2

        lifter_idx = None
        min_dist_sq = float('inf')

        # Choose bounding box closest to center
        for i, box in enumerate(frame_result.boxes):
            xyxy = box.xyxy[0]
            x1, y1, x2, y2 = xyxy
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            dist_sq = (cx - center_x_img) ** 2 + (cy - center_y_img) ** 2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                lifter_idx = i

        if lifter_idx is None:
            logger.debug(f"Frame {f_idx}: No bounding box chosen for lifter. Marking as None.")
            hip_positions.append(None)
            continue

        kpts = frame_result.keypoints[lifter_idx]
        # Check if keypoints tensor has an extra singleton dimension
        if len(kpts.xy.shape) == 3 and kpts.xy.shape[0] == 1:
            kpts_xy = kpts.xy.squeeze(0)  # Now shape becomes [17, 2]
        else:
            kpts_xy = kpts.xy

        # Ensure we have enough keypoints
        if kpts_xy.shape[0] <= RIGHT_KNEE_IDX:
            logger.debug(f"Frame {f_idx}: Not enough keypoints (<= {RIGHT_KNEE_IDX}). Marking as None.")
            hip_positions.append(None)
            continue

        left_hip_y = kpts_xy[LEFT_HIP_IDX, 1].item()
        right_hip_y = kpts_xy[RIGHT_HIP_IDX, 1].item()
        avg_hip_y = (left_hip_y + right_hip_y) / 2.0

        logger.debug(
            f"Frame {f_idx}: lifter_idx={lifter_idx}, "
            f"left_hip_y={left_hip_y}, right_hip_y={right_hip_y}, "
            f"avg_hip_y={avg_hip_y}"
        )
        hip_positions.append(avg_hip_y)

    # 2. Optional smoothing
    smoothed_hips = smooth_series(hip_positions, window_size=smoothing_window)
    logger.debug(f"Hip positions (raw): {hip_positions}")
    logger.debug(f"Hip positions (smoothed): {smoothed_hips}")

    # 3. Find local max in Y
    valid_idxs = [i for i, v in enumerate(smoothed_hips) if v is not None]
    logger.debug(f"Valid indexes: {valid_idxs}")

    if len(valid_idxs) < 3:
        logger.info("Not enough valid frames to find a turnaround. Returning None.")
        return None

    best_idx = None
    for idx_pos in range(1, len(valid_idxs) - 1):
        prev_idx = valid_idxs[idx_pos - 1]
        curr_idx = valid_idxs[idx_pos]
        next_idx = valid_idxs[idx_pos + 1]

        prev_y = smoothed_hips[prev_idx]
        curr_y = smoothed_hips[curr_idx]
        next_y = smoothed_hips[next_idx]

        if prev_y is None or curr_y is None or next_y is None:
            continue

        logger.debug(
            f"Checking local max at idx={curr_idx}: "
            f"prev_y={prev_y}, curr_y={curr_y}, next_y={next_y}"
        )
        if curr_y >= prev_y and curr_y >= next_y:
            best_idx = curr_idx
            logger.debug(f"Found local max at frame {best_idx}, curr_y={curr_y}. Breaking.")
            break

    # (Optionally) fallback to global max if no local max found
    if best_idx is None:
        logger.debug("No local max found via normal loop. Fallback: pick global max of valid frames.")
        global_max = float('-inf')
        for i in valid_idxs:
            val = smoothed_hips[i]
            if val > global_max:
                global_max = val
                best_idx = i
        logger.debug(f"Global max fallback => best_idx={best_idx}, value={global_max}")

    logger.info(f"Turnaround frame index => {best_idx}")
    return best_idx


def smooth_series(values: List[Optional[float]], window_size: int = 1) -> List[Optional[float]]:
    """
    Smooths hip positions using a simple moving average, ignoring Nones.
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

        local_vals = []
        for j in range(i - half_w, i + half_w + 1):
            if 0 <= j < len(values):
                if values[j] is not None:
                    local_vals.append(values[j])
        if not local_vals:
            smoothed[i] = None
        else:
            smoothed[i] = sum(local_vals) / len(local_vals)

    return smoothed


def check_squat_depth_at_frame(
    results: List,
    frame_idx: int,
    threshold: float = 0.0
) -> Optional[str]:
    """
    Evaluates squat depth at a single frame, logs details about hip/knee difference.
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"=== check_squat_depth_at_frame(frame_idx={frame_idx}, threshold={threshold}) ===")

    if frame_idx is None or frame_idx < 0 or frame_idx >= len(results):
        logger.debug("Invalid frame_idx. Returning None.")
        return None

    frame_result = results[frame_idx]
    if not frame_result.keypoints or not frame_result.boxes:
        logger.debug("No keypoints or boxes in chosen frame. Returning None.")
        return None

    # Identify lifter
    if hasattr(frame_result, 'orig_shape') and frame_result.orig_shape:
        orig_h, orig_w = frame_result.orig_shape
    else:
        orig_h, orig_w = 640, 640

    center_x_img = orig_w / 2
    center_y_img = orig_h / 2

    lifter_idx = None
    min_dist_sq = float('inf')
    for i, box in enumerate(frame_result.boxes):
        xyxy = box.xyxy[0]
        x1, y1, x2, y2 = xyxy
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        dist_sq = (cx - center_x_img)**2 + (cy - center_y_img)**2
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            lifter_idx = i

    if lifter_idx is None:
        logger.debug("No bounding box chosen for lifter in check_squat_depth_at_frame.")
        return None

    kpts = frame_result.keypoints[lifter_idx]
    # Remove the extra dimension if it exists
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
        f"avg_hip_y={avg_hip_y}, avg_knee_y={avg_knee_y}, best_delta={best_delta}, threshold={threshold}"
    )

    if best_delta > threshold:
        logger.debug("Frame => PASS")
        return "PASS"
    else:
        logger.debug("Frame => FAIL")
        return "FAIL"


def check_squat_depth_by_turnaround(
    results: List,
    threshold: float = 0.0
) -> str:
    """
    Uses the find_turnaround_frame to identify the "true bottom"
    and then checks squat depth on that single frame.
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"=== check_squat_depth_by_turnaround(threshold={threshold}) ===")

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
