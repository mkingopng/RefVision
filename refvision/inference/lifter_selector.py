# refvision/detection/lifter_selector.py
"""
Module for selecting the lifter detection index from YOLO detection boxes.
"""
import logging
import math
from typing import List, Optional, Any
from refvision.common.config_base import Config


logger = logging.getLogger(__name__)


def select_lifter_index(boxes: List[Any], orig_w: int, orig_h: int) -> Optional[int]:
    """
    select the index of the detection corresponding to the lifter based on
    configuration parameters
    :param boxes: (List[Any]) List of YOLO detection boxes
    :param orig_w: (int) Original width of the frame
    :param orig_h: (int) Original height of the frame
    :returns: (Optional[int]) Index of the selected detection or None if no
    detection is selected.
    """
    lifter_conf = Config.LIFTER_SELECTOR
    if lifter_conf is None:
        logger.error("lifter_selector configuration is missing in CFG.")
        return None

    expected_center = lifter_conf.get("expected_center", [0.5, 0.5])
    roi = lifter_conf.get("roi", None)
    distance_weight = lifter_conf.get("distance_weight", 1.0)
    confidence_weight = lifter_conf.get("confidence_weight", 1.0)
    lifter_id = lifter_conf.get("lifter_id", None)
    epsilon = 1e-6

    # convert expected center to pixel coordinates
    expected_cx = expected_center[0] * orig_w
    expected_cy = expected_center[1] * orig_h

    best_score = -float("inf")
    best_idx: Optional[int] = None

    for i, box in enumerate(boxes):
        # if a lifter_id is specified, select that detection immediately
        if lifter_id is not None and hasattr(box, "stack_id"):
            if box.id == lifter_id:
                logger.debug(f"Selecting detection {i} based on lifter_id {lifter_id}.")
                return i

        xyxy = box.xyxy[0]
        x1, y1, x2, y2 = xyxy
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0

        # if ROI is specified, ignore detections outside of it
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
