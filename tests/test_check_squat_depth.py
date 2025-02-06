# tests/test_check_squat_depth.py
"""
Tests for the check_squat_depth function.

To run only these tests using pytest, navigate to your project's root directory
and run one of the following commands:

  pytest tests/test_check_squat_depth.py
  pytest tests/test_check_squat_depth.py::test_check_squat_depth_pass
  pytest tests/test_check_squat_depth.py::test_check_squat_depth_fail

You can also add flags like -v, -q, or --maxfail=1 for different verbosity.

pytest tests/test_check_squat_depth.py
"""
import pytest
from typing import List, Tuple
from src.check_squat_depth import check_squat_depth
from collections import namedtuple
import numpy as np

FrameResult = namedtuple("FrameResult", ['keypoints', 'boxes', 'orig_shape'])

# we'll define a small structure for keypoints and boxes that looks like what
# yolo returns in a simplified manner
class DummyKeypoints:
	"""
    A simplified version of YOLO's keypoints output.
    This class holds a numpy-like xy array of shape (num_keypoints, 2),
    where each row corresponds to (x, y) for a particular keypoint index.
	"""
	def __init__(self, xy: List[List[float]]) -> None:
		"""
		xy will be a numpy array of shape [num_keypoints, 2]
		:param xy: A list of [x, y] pairs, one for each keypoint.
		"""
		self.xy = np.array(xy, dtype=np.float32)

class DummyBoxes:
	"""
    A simplified version of YOLO's boxes output.
    This class holds a list of bounding boxes, each defined by [x1, y1, x2, y2].
	"""
	def __init__(self, xyxy_list):
		self.xyxy = xyxy_list


def test_check_squat_depth_pass() -> None:
	"""
    Test scenario: At least one frame has hips clearly below knees, so we
    expect "PASS". We create two frames:
      - In Frame 0, the hips are above the knees (hipY < kneeY),
      - In Frame 1, the hips are below the knees (hipY > kneeY).
    Since the function scans for the best (highest hipY - kneeY),
    we should get a "PASS" if that difference is > 0.0 in any frame.
	:return: None
	"""
	# frame 0: hips are above knees +> (hip y < knee y)
	# frame 1: Hips are below knees +> (hip y > knee y)
	# we'll place the lifter near the center so that it definitely picks up lifter_idx=0
	frame0_kpts = DummyKeypoints(
		xy=[
			[0, 0],  # nose = 0
			[0, 0],  # left eye = 1
			[0, 0],  # right eye = 2
			[0, 0],  # left ear = 3
			[0, 0],  # right ear = 4
			[0, 0],  # left shoulder = 5
			[0, 0],  # right shoulder = 6
			[0, 0],  # left elbow = 7
			[0, 0],  # right elbow = 8
			[0, 0],  # left wrist = 9
			[0, 0],  # right wrist = 10
			[100, 100],  # LEFT_HIP_IDX = 11
			[120, 100],  # RIGHT_HIP_IDX = 12
			[100, 120],  # LEFT_KNEE_IDX = 13
			[120, 120],  # RIGHT_KNEE_IDX = 14
			[0, 0],  # left ankle 15
			[0, 0],  # right ankle 16
		]
	)
	frame1_kpts = DummyKeypoints(
		xy=[
			[0, 0],  # nose = 0
			[0, 0],  # left eye = 1
			[0, 0],  # right eye = 2
			[0, 0],  # left ear = 3
			[0, 0],  # right ear = 4
			[0, 0],  # left shoulder = 5
			[0, 0],  # right shoulder = 6
			[0, 0],  # left elbow = 7
			[0, 0],  # right elbow = 8
			[0, 0],  # left wrist = 9
			[0, 0],  # right wrist = 10
			[100, 130],  # LEFT_HIP_IDX = 11 => clearly below (larger y) than the knee
			[120, 130],  # RIGHT_HIP_IDX = 12
			[100, 120],  # LEFT_KNEE_IDX = 13
			[120, 120],  # RIGHT_KNEE_IDX = 14
			[0, 0],  # left ankle 15
			[0, 0],  # right ankle 16
		]
	)

	# for bounding boxes define them so their near the center
	boxes = DummyBoxes([
		[90, 90, 130, 130],  # x1, y1, x2, y2
	])

	frame0_result = FrameResult(
		keypoints=[frame0_kpts],
		boxes=[boxes],
		orig_shape=(640, 640)
	)
	frame1_result = FrameResult(
		keypoints=[frame1_kpts],
		boxes=[boxes],
		orig_shape=(640, 640)
	)

	# provide two frames
	results = [frame0_result, frame1_result]
	decision = check_squat_depth(results)
	assert decision == "PASS", f"Expected 'PASS' but got {decision}"


def test_check_squat_depth_fail() -> None:
	"""
	Test scenario: The hips never get below (or even with) the knees => difference <= 0.
    Here we only use one frame, but it doesn't matter if we used more
    as long as *all* are failing conditions. The function should return "FAIL".
	:return: None
	"""
	frame0_kpts = DummyKeypoints(
		xy=[
			[0, 0],  # nose = 0
			[0, 0],  # left eye = 1
			[0, 0],  # right eye = 2
			[0, 0],  # left ear = 3
			[0, 0],  # right ear = 4
			[0, 0],  # left shoulder = 5
			[0, 0],  # right shoulder = 6
			[0, 0],  # left elbow = 7
			[0, 0],  # right elbow = 8
			[0, 0],  # left wrist = 9
			[0, 0],  # right wrist = 10
			[100, 100],  # LEFT_HIP_IDX = 11
			[120, 100],  # RIGHT_HIP_IDX = 12
			[100, 105],  # LEFT_KNEE_IDX = 13
			[120, 105],  # RIGHT_KNEE_IDX = 14
			[0, 0],  # left ankle 15
			[0, 0],  # right ankle 16
		]
	)

	boxes = DummyBoxes([
		[90, 90, 130, 130],
	])

	frame0_result = FrameResult(
		keypoints=[frame0_kpts],
		boxes=[boxes],
		orig_shape=(640, 640)
	)

	results = [frame0_result]

	decision = check_squat_depth(results)
	assert decision == "FAIL", f"Expected 'FAIL' but got {decision}"