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
import numpy as np
from typing import List, Optional

LEFT_HIP_IDX = 11
RIGHT_HIP_IDX = 12
LEFT_KNEE_IDX = 13
RIGHT_KNEE_IDX = 14


def find_turnaround_frame(results: List, smoothing_window: int = 1) -> Optional[int]:
    """
    Identifies the frame where the lifter reaches the lowest hip position before ascending.
    Process:
      1. Extracts the average hip Y position for each frame (ignoring invalid frames).
      2. (Optional) Applies smoothing to reduce noise.
      3. Finds the local maximum Y position (the turnaround point).
    :param results: List of per-frame inference results containing keypoints and bounding boxes.
    :param smoothing_window: Window size for smoothing hip Y values (set to 1 for no smoothing).
    :return: Index of the turnaround frame, or None if a valid transition is not found.
    """
    hip_positions = []

    # Extract average hip Y position per frame
    for f_idx, frame_result in enumerate(results):
        if not frame_result.keypoints or not frame_result.boxes:
            hip_positions.append(None)
            continue

        # Identify the lifter's bounding box (select closest to center)
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
            dist_sq = (cx - center_x_img) ** 2 + (cy - center_y_img) ** 2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                lifter_idx = i

        if lifter_idx is None:
            hip_positions.append(None)
            continue

        kpts = frame_result.keypoints[lifter_idx]
        if kpts.xy.shape[0] <= RIGHT_HIP_IDX:
            hip_positions.append(None)
            continue

        left_hip_y = kpts.xy[LEFT_HIP_IDX, 1].item()
        right_hip_y = kpts.xy[RIGHT_HIP_IDX, 1].item()
        avg_hip_y = (left_hip_y + right_hip_y) / 2.0
        hip_positions.append(avg_hip_y)

    # apply optional smoothing
    smoothed_hips = smooth_series(hip_positions, window_size=smoothing_window)

    # Identify turnaround frame (local max in Y)
    valid_idxs = [i for i, v in enumerate(smoothed_hips) if v is not None]
    if len(valid_idxs) < 3:
        return None  # Not enough data to find a transition

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

        if curr_y >= prev_y and curr_y >= next_y:
            best_idx = curr_idx
            break

    return best_idx


def smooth_series(
		values: List[Optional[float]],
		window_size: int = 1) -> List[Optional[float]]:
    """
    Smooths a list of values using a simple moving average, ignoring None values.
    :param values: List of float values (or None for missing data).
    :param window_size: Number of frames for smoothing (set to 1 for no smoothing).
    :return: Smoothed list of values with the same length.
    """
    if window_size < 2:
        return values  # no smoothing needed

    smoothed = [None] * len(values)
    half_w = window_size // 2

    for i in range(len(values)):
        if values[i] is None:
            smoothed[i] = None
            continue

        local_vals = []
        for j in range(i - half_w, i + half_w + 1):
            if j < 0 or j >= len(values):
                continue
            if values[j] is not None:
                local_vals.append(values[j])
        if len(local_vals) == 0:
            smoothed[i] = None
        else:
            smoothed[i] = sum(local_vals) / len(local_vals)
    return smoothed


def check_squat_depth_at_frame(
		results: List,
		frame_idx: int,
		threshold: float = 0.0) -> Optional[str]:
    """
    Evaluates squat depth at a specific frame.
    :param results: List of frame results containing keypoints and bounding boxes.
    :param frame_idx: Index of the frame to analyze.
    :param threshold: Minimum required (hip Y - knee Y) difference to pass.
    :return: "PASS", "FAIL", or None if the frame is invalid.
    """
    if frame_idx is None or frame_idx < 0 or frame_idx >= len(results):
        return None

    frame_result = results[frame_idx]
    if not frame_result.keypoints or not frame_result.boxes:
        return None

    # Identify lifter
    if hasattr(frame_result, 'orig_shape') and frame_result.orig_shape:
        orig_h, orig_w = frame_result.orig_shape
    else:
        orig_h, orig_w = 640, 640  # default resolution

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
        return None

    kpts = frame_result.keypoints[lifter_idx]
    if kpts.xy.shape[0] <= RIGHT_KNEE_IDX:
        return None

    left_hip_y = kpts.xy[LEFT_HIP_IDX, 1].item()
    right_hip_y = kpts.xy[RIGHT_HIP_IDX, 1].item()
    left_knee_y = kpts.xy[LEFT_KNEE_IDX, 1].item()
    right_knee_y = kpts.xy[RIGHT_KNEE_IDX, 1].item()

    avg_hip_y = (left_hip_y + right_hip_y) / 2.0
    avg_knee_y = (left_knee_y + right_knee_y) / 2.0

    best_delta = avg_hip_y - avg_knee_y
    if best_delta > threshold:
        return "PASS"
    else:
        return "FAIL"


def check_squat_depth_by_turnaround(results: List, threshold: float = 0.0) -> str:
    """
    Determines squat depth by analyzing the turnaround (lowest) frame.
    :param results: List of frame results containing keypoints and bounding boxes.
    :param threshold: Minimum required (hip Y - knee Y) difference to pass.
    :return: "PASS" or "FAIL".
    """
    turnaround_idx = find_turnaround_frame(results)
    if turnaround_idx is None:
        return "FAIL"

    decision = check_squat_depth_at_frame(
		results,
		turnaround_idx,
		threshold
	)
    return decision if decision == "PASS" else "FAIL"
