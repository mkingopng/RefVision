# tests/test_lambda_handler.py
"""
poetry run pytest tests/test_lambda_handler.py
"""
import numpy as np
import json
import pytest
from refvision.lambda_handler import lambda_handler


class DummyKeypoints:
    """
    Updated DummyKeypoints that converts xy into a numpy array.
    """
    def __init__(self, xy):
        # Convert the list of keypoints to a numpy array (dtype float32).
        self.xy = np.array(xy, dtype=np.float32)

class DummyBox:
    def __init__(self, xyxy, conf, id=None):
        self.xyxy = [xyxy]
        self.conf = conf
        self.id = id

class DummyFrameResult:
    def __init__(self, keypoints, boxes, orig_shape):
        self.keypoints = keypoints
        self.boxes = boxes
        self.orig_shape = orig_shape

@pytest.fixture
def dummy_event_good_lift():
    """
    Create a dummy event simulating a "Good Lift!" outcome.
    Hips are at 150 and knees at 170, so the delta = 150 - 170 = -20,
    which is greater than a threshold of -25.
    """
    dummy_keypoints = DummyKeypoints(
        [[0, 0]] * 11 +
        [[100, 150], [120, 150]] +  # LEFT_HIP_IDX and RIGHT_HIP_IDX at y=150
        [[100, 170], [120, 170]] +  # LEFT_KNEE_IDX and RIGHT_KNEE_IDX at y=170
        [[0, 0]] * 3               # padding for remaining keypoints
    )
    dummy_box = DummyBox(xyxy=[0, 0, 640, 480], conf=0.95, id=4)
    dummy_frame = DummyFrameResult(
        keypoints=[dummy_keypoints],
        boxes=[dummy_box],
        orig_shape=(640, 480)
    )
    event = {
        "results": [dummy_frame],
        "threshold": -25.0  # With delta = -20, we expect "Good Lift!"
    }
    return event

@pytest.fixture
def dummy_event_no_lift():
    """
    Create a dummy event simulating a failing (No Lift) outcome.
    Hips are at 150 and knees at 190, so the delta = 150 - 190 = -40,
    which is not greater than the threshold of -25.
    """
    dummy_keypoints = DummyKeypoints(
        [[0, 0]] * 11 +
        [[100, 150], [120, 150]] +  # LEFT_HIP_IDX and RIGHT_HIP_IDX at y=150
        [[100, 190], [120, 190]] +  # LEFT_KNEE_IDX and RIGHT_KNEE_IDX at y=190 → delta = -40
        [[0, 0]] * 3               # padding for remaining keypoints
    )
    dummy_box = DummyBox(xyxy=[0, 0, 640, 480], conf=0.95, id=4)
    dummy_frame = DummyFrameResult(
        keypoints=[dummy_keypoints],
        boxes=[dummy_box],
        orig_shape=(640, 480)
    )
    event = {
        "results": [dummy_frame],
        "threshold": -25.0  # With delta = -40, we expect "No Lift"
    }
    return event

def test_lambda_handler_good_lift(dummy_event_good_lift):
    """
    Test the lambda_handler with a dummy event that simulates a "Good Lift!" outcome.
    :param dummy_event_good_lift:
    :return:
    """
    response = lambda_handler(dummy_event_good_lift, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "decision" in body
    assert body["decision"] == "Good Lift!", f"Expected 'Good Lift!' but got {body['decision']}"

def test_lambda_handler_no_lift(dummy_event_no_lift):
    """
    Test the lambda_handler with a dummy event that simulates a failing (No Lift) outcome.
    :param dummy_event_no_lift:
    :return:
    """
    response = lambda_handler(dummy_event_no_lift, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "decision" in body
    assert body["decision"] == "No Lift", f"Expected 'No Lift' but got {body['decision']}"
