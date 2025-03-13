# tests/test_depth_checker.py
"""
module for testing depth_checker functions.
"""
import numpy as np
from config.config import CFG
from typing import Any, Optional, cast
from refvision.analysis.depth_checker import (
    check_squat_depth_at_frame,
    check_squat_depth_by_turnaround,
)
from refvision.detection import lifter_selector as ls_mod


class DummyCFG(CFG):
    """
    Dummy configuration used for testing.
    """

    lifter_selector: dict[str, Any] = {
        "expected_center": [0.5, 0.5],
        "roi": [0.0, 0.0, 1.0, 1.0],
        "distance_weight": 1.0,
        "confidence_weight": 1.0,
        "lifter_id": None,
    }


dummy_cfg = DummyCFG()
ls_mod.CFG.lifter_selector = dummy_cfg.lifter_selector


class DummyKeypoints:
    """
    Dummy class to simulate keypoints.
    """

    def __init__(self, xy: np.ndarray) -> None:
        self.xy = xy


class DummyFrameResult:
    """
    Dummy class to simulate frame results.
    """

    def __init__(self, keypoints: list, boxes: list, orig_shape=(640, 640)) -> None:
        self.keypoints = keypoints
        self.boxes = boxes
        self.orig_shape = orig_shape


class DummyBox:
    """
    Dummy class to simulate detection boxes.
    """

    def __init__(self, xyxy: Any, conf: float, id: Optional[int] = None) -> None:
        self.xyxy = [xyxy]
        self.conf = conf
        self.id = id


def create_dummy_frame(hip_y: float, knee_y: float) -> DummyFrameResult:
    """
    create a dummy frame result with given hip and knee y-coordinates.
    :param hip_y: hip y-coordinate
    :param knee_y: knee y-coordinate
    :return: dummy frame result
    """
    # create a dummy keypoints array with shape (17, 2)
    kpts_arr = np.zeros((17, 2), dtype=float)
    # set hips coordinates
    kpts_arr[11, 1] = hip_y
    kpts_arr[12, 1] = hip_y
    # set knees coordinates
    kpts_arr[13, 1] = knee_y
    kpts_arr[14, 1] = knee_y
    keypoints = [DummyKeypoints(xy=kpts_arr)]
    boxes = [DummyBox(xyxy=(0, 0, 10, 10), conf=0.9)]
    return DummyFrameResult(keypoints=keypoints, boxes=boxes)


def test_check_squat_depth_at_frame_good_lift() -> None:
    """
    For a "Good Lift!", the hip-to-knee delta should exceed the THRESHOLD.
    :return: None
    """
    frame = create_dummy_frame(hip_y=410, knee_y=380)  # delta = 30
    result_dict = cast(dict, check_squat_depth_at_frame([frame], 0))
    assert result_dict["decision"] == "Good Lift!"


def test_check_squat_depth_at_frame_no_lift() -> None:
    """
    For a "No Lift", the hip-to-knee delta should not exceed the THRESHOLD.
    :return: None
    """
    frame = create_dummy_frame(hip_y=400, knee_y=410)  # delta = -10
    result_dict = cast(dict, check_squat_depth_at_frame([frame], 0))
    assert result_dict["decision"] == "No Lift"


def test_check_squat_depth_by_turnaround() -> None:
    """
    Create multiple frames and ensure the turnaround frame (with best depth) is
    chosen.
    :return: None
    """
    frame1 = create_dummy_frame(hip_y=400, knee_y=380)  # delta = 20 (bad lift)
    frame2 = create_dummy_frame(hip_y=500, knee_y=450)  # delta = 50 (good lift)
    frames = [frame1, frame2]
    result_dict = cast(dict, check_squat_depth_by_turnaround(frames))
    assert result_dict["decision"] == "Good Lift!"
