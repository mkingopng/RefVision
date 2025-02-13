# refvision/find_critical_frame.py
"""
Module for identifying the turnaround (bottom) frame in a squat video
and checking squat depth at that frame.
"""
import logging
import math
from typing import List, Optional
from config.config import CFG


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/debug.log", mode="w"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

LEFT_HIP_IDX = 11
RIGHT_HIP_IDX = 12
LEFT_KNEE_IDX = 13
RIGHT_KNEE_IDX = 14


def select_lifter_index(boxes, orig_w, orig_h):
    """
    Select the index of the detection corresponding to the lifter based on
    configuration parameters.
    :param boxes: List of YOLO detection boxes.
    :param orig_w: Original width of the frame.
    :param orig_h: Original height of the frame.
    :returns: Index of the selected detection or None if no detection is selected.
    """
    lifter_conf = CFG.lifter_selector
    if lifter_conf is None:
        logger.error("lifter_selector configuration is missing in CFG.")
        return None

    expected_center = lifter_conf.get("expected_center", [0.5, 0.5])
    roi = lifter_conf.get("roi", None)
    distance_weight = lifter_conf.get("distance_weight", 1.0)
    confidence_weight = lifter_conf.get("confidence_weight", 1.0)
    lifter_id = lifter_conf.get("lifter_id", None)
    epsilon = 1e-6

    # Convert expected center to pixel coordinates.
    expected_cx = expected_center[0] * orig_w
    expected_cy = expected_center[1] * orig_h

    best_score = -float("inf")
    best_idx = None

    for i, box in enumerate(boxes):
        # If a lifter_id is specified, select that detection immediately.
        if lifter_id is not None and hasattr(box, "id"):
            if box.id == lifter_id:
                logger.debug(f"Selecting detection {i} based on lifter_id {lifter_id}.")
                return i

        xyxy = box.xyxy[0]
        x1, y1, x2, y2 = xyxy
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0

        # If ROI is specified, ignore detections outside of it.
        if roi is not None:
            roi_x1 = roi[0] * orig_w
            roi_y1 = roi[1] * orig_h
            roi_x2 = roi[2] * orig_w
            roi_y2 = roi[3] * orig_h
            if not (roi_x1 <= cx <= roi_x2 and roi_y1 <= cy <= roi_y2):
                continue

        dist = math.sqrt((cx - expected_cx) ** 2 + (cy - expected_cy) ** 2)
        score = (confidence_weight * box.conf) / (distance_weight * (dist + epsilon))
        if score > best_score:
            best_score = score
            best_idx = i

    logger.debug(f"Selected detection index {best_idx} with score {best_score}.")
    return best_idx


def find_turnaround_frame(
    results: List,
    smoothing_window: int = 1
) -> Optional[int]:
    """
    Identifies the frame where the lifter reaches their lowest hip position
    (i.e. the highest y value) in the video. This method uses the global maximum
    of the (optionally smoothed) hip positions.
    :param results: List of frame results from YOLO inference.
    :param smoothing_window: Size of the moving average window for smoothing.
    :returns: The index (int) of the turnaround frame or None if not found.
    """
    logger.debug("=== find_turnaround_frame called ===")
    hip_positions = []

    for f_idx, frame_result in enumerate(results):
        # skip frames with no keypoints or boxes.
        if not frame_result.keypoints or not frame_result.boxes:
            logger.debug(f"Frame {f_idx}: No keypoints or boxes. Marking as None.")
            hip_positions.append(None)
            continue

        # determine original frame dimensions.
        if hasattr(frame_result, 'orig_shape') and frame_result.orig_shape:
            orig_h, orig_w = frame_result.orig_shape
        else:
            orig_h, orig_w = 640, 640

        # use helper function to choose the lifter detection.
        lifter_idx = select_lifter_index(frame_result.boxes, orig_w, orig_h)
        if lifter_idx is None:
            logger.debug(f"Frame {f_idx}: No lifter selected. Marking as None.")
            hip_positions.append(None)
            continue

        kpts = frame_result.keypoints[lifter_idx]
        if len(kpts.xy.shape) == 3 and kpts.xy.shape[0] == 1:
            kpts_xy = kpts.xy.squeeze(0)
        else:
            kpts_xy = kpts.xy

        if kpts_xy.shape[0] <= RIGHT_KNEE_IDX:
            logger.debug(f"Frame {f_idx}: Not enough keypoints. Marking as None.")
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

    smoothed_hips = smooth_series(hip_positions, window_size=smoothing_window)
    logger.debug(f"Hip positions (raw): {hip_positions}")
    logger.debug(f"Hip positions (smoothed): {smoothed_hips}")

    valid_idxs = [i for i, v in enumerate(smoothed_hips) if v is not None]
    logger.debug(f"Valid indexes: {valid_idxs}")
    if not valid_idxs:
        logger.info("No valid frames to determine a turnaround. Returning None.")
        return None

    best_idx = max(valid_idxs, key=lambda i: smoothed_hips[i])
    logger.info(f"Turnaround frame index (global max) => {best_idx}")
    return best_idx


def smooth_series(
        values: List[Optional[float]],
        window_size: int = 1
) -> List[Optional[float]]:
    """
    Smooths a series of hip position values using a simple moving average.
    :param values: List of hip positions (or None).
    :param window_size: Size of the moving average window.
    :returns: A list of smoothed values.
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
    results: List,
    frame_idx: int,
    threshold: float = -30.0
) -> Optional[str]:
    """
    Evaluates squat depth at a given frame by comparing the average hip and knee positions.
    :param results: List of frame results from YOLO inference.
    :param frame_idx: Index of the frame to evaluate.
    :param threshold: Depth threshold for a “Good Lift!” (squat is deep enough).
    :returns: "Good Lift!" if the squat meets the threshold; else "No Lift"
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

    if hasattr(frame_result, 'orig_shape') and frame_result.orig_shape:
        orig_h, orig_w = frame_result.orig_shape
    else:
        orig_h, orig_w = 640, 640

    lifter_idx = select_lifter_index(
        frame_result.boxes,
        orig_w,
        orig_h
    )

    if lifter_idx is None:
        logger.debug("No lifter detected in selected frame. Returning None.")
        return None

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
        f"avg_hip_y={avg_hip_y}, avg_knee_y={avg_knee_y}, best_delta={best_delta}, threshold={threshold}"
    )
    if best_delta > threshold:
        logger.debug("Frame => Good Lift!")
        return "Good Lift!"
    else:
        logger.debug("Frame => No Lift")
        return "No Lift"


def check_squat_depth_by_turnaround(
    results: List,
    threshold: float = 0.0
) -> str:
    """
    Uses find_turnaround_frame to select the squat’s bottom frame and then
    evaluates the squat depth.
    :param results: List of frame results from YOLO inference.
    :param threshold: Depth threshold for a “Good Lift!”.
    :returns: "Good Lift!" if the squat is deep enough; otherwise "No Lift".
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"=== check_squat_depth_by_turnaround(threshold={threshold}) ===")
    turnaround_idx = find_turnaround_frame(results)
    logger.debug(f"Turnaround frame => {turnaround_idx}")
    if turnaround_idx is None:
        logger.info("No valid turnaround frame found, returning No Lift.")
        return "No Lift"
    decision = check_squat_depth_at_frame(results, turnaround_idx, threshold)
    logger.debug(f"Decision from turnaround frame => {decision}")
    final = decision if decision == "Good Lift!" else "No Lift"
    logger.info(f"check_squat_depth_by_turnaround => {final}")
    return final
