# tests/test_find_critical_frame.py
"""
Unit tests for finding the critical (turnaround) frame and checking squat depth.

Run these tests using:
    pytest tests/test_find_critical_frame.py
"""
import numpy as np
from typing import List
from collections import namedtuple
from refvision.analysis.turnaround_detector import find_turnaround_frame
from refvision.analysis.depth_checker import check_squat_depth_by_turnaround

FrameResult = namedtuple("FrameResult", ["keypoints", "boxes", "orig_shape"])


class DummyKeypoints:
    """
    A simple keypoints class for testing simulating YOLO output.
    Stores keypoints as a numpy array in (x, y) format.
    """

    def __init__(self, xy: List[List[float]]) -> None:
        self.xy = np.array(xy, dtype=np.float32)


class DummyBoxes:
    """
    A simplified bounding box class for testing, simulating YOLO output.
    Stores bounding boxes as a list of [x1, y1, x2, y2] values.
    """

    def __init__(self, xyxy_list: list[list[float]], conf: float = 1.0):
        self.xyxy = xyxy_list
        self.conf = conf


def test_find_turnaround_frame():
    """
    Tests whether `find_turnaround_frame` correctly identifies the turnaround
    point. The hip Y position increases, reaches a peak, and then decreases.
    Expected turnaround frame: index 2 (hip Y = 130).
    """
    frames = []
    hip_values = [100, 110, 130, 120, 110]  # peak at index 2

    for val in hip_values:
        # Use a box whose center is (320,320) so that it lies within the ROI.
        boxes = DummyBoxes([[300, 300, 340, 340]])
        kpts = DummyKeypoints(
            [[0, 0]] * 11  # padding for unused keypoints
            + [
                [100, val],  # LEFT_HIP_IDX=11
                [120, val],  # RIGHT_HIP_IDX=12
                [100, 0],  # LEFT_KNEE_IDX=13 (not important here)
                [120, 0],  # RIGHT_KNEE_IDX=14
                [0, 0],  # ankle 15
                [0, 0],  # ankle 16
            ]
        )
        frames.append(
            FrameResult(keypoints=[kpts], boxes=[boxes], orig_shape=(640, 640))
        )

    turnaround = find_turnaround_frame(frames)
    assert turnaround == 2, f"Expected turnaround at frame 2, got {turnaround}"


def test_check_squat_depth_by_turnaround_pass():
    """
    Tests if `check_squat_depth_by_turnaround` returns "Good Lift!" when the lowest frame
    (turnaround frame) has hips below knees.
    """
    frames = []

    # For bounding box near center
    def make_frame(hip_val: float) -> FrameResult:
        # Use a box that produces a valid detection.
        boxes = DummyBoxes([[300.0, 300.0, 340.0, 340.0]], conf=0.9)
        kpts = DummyKeypoints(
            [[0.0, 0.0]] * 11  # padding
            + [
                [100.0, hip_val],  # LEFT_HIP_IDX
                [120.0, hip_val],  # RIGHT_HIP_IDX
                [100.0, 120.0],  # LEFT_KNEE_IDX
                [120.0, 120.0],  # RIGHT_KNEE_IDX
                [0.0, 0.0],  # LEFT_ANKLE_IDX
                [0.0, 0.0],
            ]
        )
        return FrameResult(keypoints=[kpts], boxes=[boxes], orig_shape=(640, 640))

    frames.append(make_frame(100))  # ascending
    frames.append(make_frame(130))  # top
    frames.append(make_frame(125))  # descending

    decision = check_squat_depth_by_turnaround(frames, threshold=0.0)
    assert decision == "Good Lift!", f"Expected 'Good Lift!' but got {decision}"


def test_check_squat_depth_by_turnaround_fail() -> None:
    """
    Tests if `check_squat_depth_by_turnaround` returns "FAIL" when the lowest
    (turnaround) frame never has hips below knees.
    """
    frames = []

    def make_frame(hip_val: float, knee_val: float) -> FrameResult:
        boxes = DummyBoxes(
            [[300.0, 300.0, 340.0, 340.0]], conf=0.9
        )  # valid bounding box
        kpts = DummyKeypoints(
            [[0.0, 0.0]] * 11  # padding
            + [
                [100.0, hip_val],  # LEFT_HIP_IDX
                [120.0, hip_val],  # RIGHT_HIP_IDX
                [100.0, knee_val],  # LEFT_KNEE_IDX
                [120.0, knee_val],  # RIGHT_KNEE_IDX
                [0.0, 0.0],  # LEFT_ANKLE_IDX
                [0.0, 0.0],
            ]
        )
        return FrameResult(keypoints=[kpts], boxes=[boxes], orig_shape=(640, 640))

    frames.append(make_frame(100, 105))  # ascending
    frames.append(make_frame(110, 112))  # top, but not "below"
    frames.append(make_frame(105, 107))  # descending

    decision = check_squat_depth_by_turnaround(frames, threshold=0.0)
    # Update the expected output to "No Lift" if that is what your function returns.
    assert decision == "No Lift", f"Expected 'No Lift' but got {decision}"
