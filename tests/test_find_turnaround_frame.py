# tests/test_find_turnaround_frame.py
"""
Tests for the turnaround detector.
"""

import pytest
from unittest.mock import patch
import numpy as np
import refvision.inference.lifter_selector as ls_mod
import refvision.analysis.find_turnaround_frame as ftf_mod
from refvision.analysis.find_turnaround_frame import find_turnaround_frame


@pytest.fixture
def mock_cfg():
    fake_cfg = {
        "LEFT_HIP_IDX": 11,
        "RIGHT_HIP_IDX": 12,
        "LEFT_KNEE_IDX": 13,
        "RIGHT_KNEE_IDX": 14,
        "THRESHOLD": 0.0,
        "LIFTER_SELECTOR": {
            "expected_center": [0.5, 0.5],
            "roi": [0.0, 0.0, 1.0, 1.0],
            "distance_weight": 1.0,
            "confidence_weight": 1.0,
            "lifter_id": None,
        },
    }
    with patch.object(ftf_mod, "cfg", fake_cfg), patch.object(ls_mod, "cfg", fake_cfg):
        yield


class DummyKeypoints:
    """Simple test class to mimic YOLO keypoints structure."""

    def __init__(self, xy: list[list[float]]) -> None:
        self.xy = np.array(xy, dtype=np.float32)


class DummyBoxes:
    """Simple test class to mimic YOLO detection boxes."""

    def __init__(self, xyxy_list: list[list[float]], conf: float = 1.0):
        self.xyxy = xyxy_list
        self.conf = conf


class FrameResult:
    """Mimic YOLO's results for a single frame."""

    def __init__(
        self,
        keypoints: list[DummyKeypoints],
        boxes: list[DummyBoxes],
        orig_shape: tuple[int, int] = (640, 640),
    ):
        self.keypoints = keypoints
        self.boxes = boxes
        self.orig_shape = orig_shape


def test_find_turnaround_frame_peak_detection(mock_cfg):
    """
    Tests whether find_turnaround_frame identifies frame with highest hip Y.
    Expect the peak at index 2 if the hip values are [100, 110, 130, 120, 110].
    """
    frames = []
    hip_vals = [100.0, 110.0, 130.0, 120.0, 110.0]
    for val in hip_vals:
        # bounding box (center ~ (320,320)) => inside ROI
        boxes = DummyBoxes([[300.0, 300.0, 340.0, 340.0]], conf=0.9)
        # Indices 11 & 12 = hips => set them to val
        # Everything must be float, or Mypy complains.
        xy = [[0.0, 0.0]] * 11 + [
            [100.0, val],  # LEFT_HIP_IDX=11
            [120.0, val],  # RIGHT_HIP_IDX=12
            [100.0, 0.0],
            [120.0, 0.0],
        ]
        kpts = DummyKeypoints(xy)
        frames.append(FrameResult([kpts], [boxes], (640, 640)))

    turnaround_index = find_turnaround_frame(frames)
    assert turnaround_index == 2, f"Expected 2, got {turnaround_index}"


def test_find_turnaround_frame_with_invalid_frames(mock_cfg):
    """Check skipping frames that have no keypoints or boxes."""
    # invalid frame => no boxes or keypoints
    invalid_frame = FrameResult([], [])
    # valid frame => has box + hip=300
    boxes = DummyBoxes([[300.0, 300.0, 340.0, 340.0]], conf=0.9)
    xy = [[0.0, 0.0]] * 11 + [
        [100.0, 300.0],
        [120.0, 300.0],
        [100.0, 0.0],
        [120.0, 0.0],
    ]
    kpts = DummyKeypoints(xy)
    valid_frame = FrameResult([kpts], [boxes], (640, 640))

    frames = [invalid_frame, valid_frame]
    idx = find_turnaround_frame(frames)
    assert idx == 1, f"Expected index=1 for the valid frame, got {idx}"
