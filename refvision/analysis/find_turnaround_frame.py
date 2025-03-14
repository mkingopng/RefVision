# refvision/analysis/find_turnaround_frame.py
"""
Module for detecting the turnaround (bottom) frame in a squat video
"""
import logging
from typing import List, Optional, Any, cast
from refvision.inference.lifter_selector import select_lifter_index
from refvision.utils.series_utils import smooth_series
from refvision.common.config_base import Config


def find_turnaround_frame(
    results: List[Any], smoothing_window: int = 1
) -> Optional[int]:
    """
    Identifies the frame where the lifter reaches their lowest hip position
    (i.e. the highest y value) in the video.
    :param results: (List[Any]) List of frame results from YOLO inference.
    :param smoothing_window: (int) Size of the moving average window for smoothing.
    :returns: (Optional[int]) The index of the turnaround frame or None if not
    found.
    """
    logger = logging.getLogger(__name__)
    logger.debug("=== find_turnaround_frame called ===")
    hip_positions: List[Optional[float]] = []

    for f_idx, frame_result in enumerate(results):
        # skip frames with no keypoints or boxes.
        if not frame_result.keypoints or not frame_result.boxes:
            logger.debug(f"Frame {f_idx}: No keypoints or boxes. Marking as None.")
            hip_positions.append(None)
            continue

        # determine original frame dimensions.
        if hasattr(frame_result, "orig_shape") and frame_result.orig_shape:
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

        if kpts_xy.shape[0] <= Config.RIGHT_HIP_IDX:
            logger.debug(f"Frame {f_idx}: Not enough keypoints. Marking as None.")
            hip_positions.append(None)
            continue

        left_hip_y = kpts_xy[Config.LEFT_HIP_IDX, 1].item()
        right_hip_y = kpts_xy[Config.RIGHT_HIP_IDX, 1].item()
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

    best_idx = max(
        valid_idxs,
        key=lambda i: (
            float(cast(float, smoothed_hips[i]))
            if smoothed_hips[i] is not None
            else float("-inf")
        ),
    )

    logger.info(f"Turnaround frame index (global max) => {best_idx}")
    return best_idx
