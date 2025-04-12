# tests/test_depth_checker.py
"""
module for testing depth_checker functions.
"""
import numpy as np
import pytest
from typing import cast, Any
from unittest.mock import patch

import refvision.analysis.depth_checker as dc_mod
import refvision.analysis.lifter_selector as ls_mod

from refvision.analysis.depth_checker import (
    check_squat_depth_at_frame,
    check_squat_depth_by_turnaround,
)


class DummyKeypoints:
    """Fake class to simulate key points."""

    def __init__(self, xy: np.ndarray) -> None:
        self.xy = xy


class DummyBox:
    """Fake class to simulate detection boxes."""

    def __init__(self, xyxy: Any, conf: float, id: int | None = None) -> None:
        self.xyxy = [xyxy]
        self.conf = conf
        self.id = id


class DummyFrameResult:
    """Dummy class to simulate a YOLO result for one frame."""

    def __init__(
        self, keypoints: list[Any], boxes: list[Any], orig_shape=(640, 640)
    ) -> None:
        self.keypoints = keypoints
        self.boxes = boxes
        self.orig_shape = orig_shape


def create_dummy_frame(hip_y: float, knee_y: float) -> DummyFrameResult:
    """Create a dummy frame result with given hip and knee y-coordinates."""
    # shape (17, 2) for all keypoints (COCO style indexing)
    kpts_arr = np.zeros((17, 2), dtype=float)
    # set hips
    kpts_arr[11, 1] = hip_y
    kpts_arr[12, 1] = hip_y
    # set knees
    kpts_arr[13, 1] = knee_y
    kpts_arr[14, 1] = knee_y

    keypoints = [DummyKeypoints(kpts_arr)]
    boxes = [DummyBox(xyxy=(0, 0, 10, 10), conf=0.9)]
    return DummyFrameResult(keypoints=keypoints, boxes=boxes)


@pytest.fixture
def mock_cfg():
    """
    Fixture to patch the 'cfg' dictionary in both depth_checker.py and
    lifter_selector.py so the test can supply custom thresholds or
    'LIFTER_SELECTOR' data.
    """
    fake_cfg = {
        "THRESHOLD": 0.0,
        "LEFT_HIP_IDX": 11,
        "RIGHT_HIP_IDX": 12,
        "LEFT_KNEE_IDX": 13,
        "RIGHT_KNEE_IDX": 14,
        "LIFTER_SELECTOR": {
            "expected_center": [0.5, 0.5],
            "roi": [0.0, 0.0, 1.0, 1.0],
            "distance_weight": 1.0,
            "confidence_weight": 1.0,
            "lifter_id": None,
        },
    }

    with patch.object(dc_mod, "cfg", fake_cfg), patch.object(ls_mod, "cfg", fake_cfg):
        yield  # run the test with these patches in place


def test_check_squat_depth_at_frame_good_lift(mock_cfg) -> None:
    """
    For a "Good Lift!", the hip-to-knee delta should exceed the THRESHOLD (0.0).
    """
    frame = create_dummy_frame(hip_y=410, knee_y=380)  # delta = +30
    result_dict = cast(dict, check_squat_depth_at_frame([frame], 0))
    assert result_dict is not None
    assert result_dict["decision"] == "Good Lift!"


def test_check_squat_depth_at_frame_no_lift(mock_cfg) -> None:
    """
    For a "No Lift", the hip-to-knee delta should not exceed the THRESHOLD (0.0).
    """
    frame = create_dummy_frame(hip_y=400, knee_y=410)  # delta = -10
    result_dict = cast(dict, check_squat_depth_at_frame([frame], 0))
    assert result_dict is not None
    assert result_dict["decision"] == "No Lift"


def test_check_squat_depth_by_turnaround(mock_cfg) -> None:
    """
    Create multiple frames and ensure the turnaround frame (with best depth) is chosen.
    The second frame has a bigger (hip_y - knee_y), so it should be 'Good Lift!'.
    """
    frame1 = create_dummy_frame(hip_y=400, knee_y=380)  # delta=+20 => "Good Lift!"
    frame2 = create_dummy_frame(hip_y=500, knee_y=450)  # delta=+50 => definitely Good
    frames = [frame1, frame2]
    result_dict = cast(dict, check_squat_depth_by_turnaround(frames))
    assert result_dict["decision"] == "Good Lift!"
    assert result_dict["turnaround_frame"] == 1  # second frame is deeper
