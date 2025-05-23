# refvision/analysis/depth_checker.py
"""
Module for checking squat depth at a given frame or by using the turnaround
frame.
"""
import logging
from typing import List, Optional, Any
from refvision.analysis.lifter_selector import select_lifter_index
from refvision.common.config import get_config
from refvision.utils.timer import measure_time

cfg = get_config()


@measure_time
def check_squat_depth_at_frame(
    results: List[Any], frame_idx: int, threshold: float = cfg["THRESHOLD"]
) -> Optional[dict]:
    """
    Evaluates squat depth at a given frame by comparing the average hip and
    knee positions.
    :param results: (List[Any]) List of frame results from YOLO inference.
    :param frame_idx: (int) Index of the frame to evaluate
    :param threshold: (float) Depth THRESHOLD for a “Good Lift!”
    :returns: (Optional[str]) "Good Lift!" if the squat meets the THRESHOLD;
    "No Lift" otherwise, or None if invalid.
    """
    logger = logging.getLogger(__name__)
    logger.debug(
        f"=== check_squat_depth_at_frame(frame_idx={frame_idx}, THRESHOLD={threshold}) ==="
    )
    if frame_idx is None or frame_idx < 0 or frame_idx >= len(results):
        logger.debug("Invalid frame_idx. Returning None.")
        return None

    frame_result = results[frame_idx]
    if not frame_result.keypoints or not frame_result.boxes:
        logger.debug("No keypoints or boxes in chosen frame. Returning None.")
        return None

    if hasattr(frame_result, "orig_shape") and frame_result.orig_shape:
        orig_h, orig_w = frame_result.orig_shape
    else:
        orig_h, orig_w = 640, 640

    lifter_idx = select_lifter_index(frame_result.boxes, orig_w, orig_h)
    if lifter_idx is None:
        logger.debug("No lifter detected in selected frame. Returning None.")
        return None

    kpts = frame_result.keypoints[lifter_idx]
    if len(kpts.xy.shape) == 3 and kpts.xy.shape[0] == 1:
        kpts_xy = kpts.xy.squeeze(0)
    else:
        kpts_xy = kpts.xy

    if kpts_xy.shape[0] <= cfg["RIGHT_KNEE_IDX"]:
        logger.debug("Not enough keypoints to retrieve hips/knees.")
        return None

    left_hip_y = kpts_xy[cfg["LEFT_HIP_IDX"], 1].item()
    right_hip_y = kpts_xy[cfg["RIGHT_HIP_IDX"], 1].item()
    left_knee_y = kpts_xy[cfg["LEFT_KNEE_IDX"], 1].item()
    right_knee_y = kpts_xy[cfg["RIGHT_KNEE_IDX"], 1].item()

    avg_hip_y = (left_hip_y + right_hip_y) / 2.0
    avg_knee_y = (left_knee_y + right_knee_y) / 2.0
    best_delta = avg_hip_y - avg_knee_y

    logger.debug(
        f"Frame {frame_idx}: left_hip_y={left_hip_y}, right_hip_y={right_hip_y}, "
        f"left_knee_y={left_knee_y}, right_knee_y={right_knee_y}, "
        f"avg_hip_y={avg_hip_y}, avg_knee_y={avg_knee_y}, best_delta={best_delta}, THRESHOLD={threshold}"
    )
    decision = "Good Lift!" if best_delta > threshold else "No Lift"
    return {
        "decision": decision,
        "turnaround_frame": frame_idx,
        "keypoints": {
            "left hip y": left_hip_y,
            "right hip y": right_hip_y,
            "left knee y": left_knee_y,
            "right knee y": right_knee_y,
            "average hip y": avg_hip_y,
            "average knee y": avg_knee_y,
            "best delta": best_delta,
        },
    }


@measure_time
def check_squat_depth_by_turnaround(
    results: List[Any], threshold: float = cfg["THRESHOLD"]
) -> dict:
    """
    uses find_turnaround_frame to select the squat’s bottom frame and then
    evaluates the squat depth.
    :param results: (List[Any]) List of frame results from YOLO inference
    :param threshold: (float): Depth THRESHOLD for a “Good Lift!”
    :returns: (str) "Good Lift!" if the squat is deep enough; else "No Lift".
    """
    import refvision.analysis.find_turnaround_frame as td  # import here to avoid circular dependency.

    logger = logging.getLogger(__name__)
    logger.debug(f"=== check_squat_depth_by_turnaround(THRESHOLD={threshold}) ===")
    turnaround_idx = td.find_turnaround_frame(results)

    logger.debug(f"Turnaround frame => {turnaround_idx}")

    if turnaround_idx is None:
        logger.info("No valid turnaround frame found, returning No Lift.")
        return {"decision": "No Lift", "turnaround_frame": None, "keypoints": {}}

    result = check_squat_depth_at_frame(results, turnaround_idx, threshold)

    if not result:
        return {
            "decision": "No Lift",
            "turnaround_frame": turnaround_idx,
            "keypoints": {},
        }

    logger.debug(f"Decision from turnaround frame => {result['decision']}")
    final = result["decision"] if result["decision"] == "Good Lift!" else "No Lift"
    logger.info(f"check_squat_depth_by_turnaround => {final}")

    return result


# todo: I'd like to improve the annotation for the skeleton that is created.
#  For example, to calculate the joint angles at the knee. How can i do that?
