# refvision/lambda_handler.py
"""
usage: poetry run python -m refvision.lambda_handler
"""
import json
from refvision.find_critical_frame import check_squat_depth_by_turnaround

# Dummy classes to simulate a YOLO result
class DummyKeypoints:
    def __init__(self, xy):
        # Expect xy to be a NumPy array or list of lists (for simplicity, use list here)
        self.xy = xy

class DummyBox:
    def __init__(self, xyxy, conf, id=None):
        self.xyxy = [xyxy]
        self.conf = conf
        self.id = id

class DummyFrameResult:
    def __init__(self, keypoints, boxes, orig_shape):
        self.keypoints = keypoints  # a list (for example, one element)
        self.boxes = boxes          # a list (for example, one element)
        self.orig_shape = orig_shape

def lambda_handler(event, context):
    """
    Expects an event that contains the key "results" with a list representing
    frame results.
    """
    results = event.get("results", [])
    threshold = event.get("threshold", 0.0)
    decision = check_squat_depth_by_turnaround(results, threshold)
    return {
        "statusCode": 200,
        "body": json.dumps({"decision": decision})
    }

if __name__ == "__main__":
    # Create a dummy frame result that would trigger a "Good Lift!" decision.
    # For example, assume the dummy keypoints indicate hips are below knees.
    # (Using the indices defined in your module: LEFT_HIP_IDX=11, RIGHT_HIP_IDX=12,
    #  LEFT_KNEE_IDX=13, RIGHT_KNEE_IDX=14)
    dummy_keypoints = DummyKeypoints(
        # Create a dummy 17x2 list; indices 11 and 12 are hips, 13 and 14 are knees.
        # We'll fill with dummy values so that (hip_y - knee_y) is above threshold.
        [[0, 0]] * 11 +
        [[100, 150], [120, 150]] +  # hips (at y=150)
        [[100, 170], [120, 170]] +  # knees (at y=170) → delta = -20, so adjust threshold accordingly
        [[0, 0]] * 3  # the rest
    )
    dummy_box = DummyBox(xyxy=[0, 0, 640, 480], conf=0.95, id=4)
    dummy_frame = DummyFrameResult(
        keypoints=[dummy_keypoints],
        boxes=[dummy_box],
        orig_shape=(640, 480)
    )
    dummy_event = {
        "results": [dummy_frame],  # list with one frame result
        "threshold": -25.0  # set threshold so that (150-170=-20) > -25.0 returns PASS ("Good Lift!")
    }
    print(lambda_handler(dummy_event, None))
