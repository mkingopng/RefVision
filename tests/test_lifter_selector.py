# tests/test_lifter_selector.py
"""
Tests for the lifter_selector module
"""
import pytest
from unittest.mock import patch
from typing import Optional, Any, List
import refvision.analysis.lifter_selector as ls_mod
from refvision.analysis.lifter_selector import select_lifter_index


class DummyBox:
    """
    Fake class to simulate a YOLO detection box.
    Each box has a .xyxy list, .conf, and optional .id
    """

    def __init__(self, xyxy: Any, conf: float, box_id: Optional[int] = None) -> None:
        self.xyxy = [xyxy]
        self.conf = conf
        self.id = box_id


@pytest.fixture
def mock_cfg():
    """
    A fixture that patches ls_mod.cfg so select_lifter_index sees our fake LIFTER_SELECTOR.
    You can mutate the dictionary inside each test to change 'lifter_id' or 'roi' etc.
    """
    fake_cfg = {
        "LIFTER_SELECTOR": {
            "expected_center": [0.5, 0.5],
            "roi": [0.0, 0.0, 1.0, 1.0],
            "distance_weight": 1.0,
            "confidence_weight": 1.0,
            "lifter_id": None,
        }
    }

    with patch.object(ls_mod, "cfg", fake_cfg):
        yield fake_cfg


def test_select_lifter_index_basic(mock_cfg) -> None:
    """
    Test basic functionality: with default config, the detection
    that's closer to the center (and/or higher conf) should be chosen.
    """
    boxes: List[DummyBox] = [
        DummyBox(xyxy=(0, 0, 10, 10), conf=0.8),
        DummyBox(xyxy=(30, 30, 40, 40), conf=0.9),
    ]
    # the second box is presumably "better" (closer to center or higher conf).
    idx = select_lifter_index(boxes, orig_w=640, orig_h=640)
    assert idx == 1


def test_select_lifter_index_with_lifter_id(mock_cfg) -> None:
    """
    If lifter_id is set, and a matching box .id is found, we pick that immediately.
    """
    # override the lifter_id in the patched config
    mock_cfg["LIFTER_SELECTOR"]["lifter_id"] = 42

    boxes: List[DummyBox] = [
        DummyBox(xyxy=(0, 0, 10, 10), conf=0.8, box_id=1),
        DummyBox(xyxy=(30, 30, 40, 40), conf=0.9, box_id=42),
    ]
    idx = select_lifter_index(boxes, orig_w=640, orig_h=640)
    assert idx == 1

    # Clean up
    mock_cfg["LIFTER_SELECTOR"]["lifter_id"] = None


def test_select_lifter_index_roi(mock_cfg) -> None:
    """
    If ROI is specified, boxes outside that region are ignored.
    """
    # set a narrower ROI in the patched config
    mock_cfg["LIFTER_SELECTOR"]["roi"] = [0.1, 0.1, 0.9, 0.9]
    # in pixels for a 640x640 frame, that’s (64,64) to (576,576)

    boxes: List[DummyBox] = [
        # this box is near (5,5)-(10,10), i.e. center ~ (7.5,7.5), which is outside the ROI
        DummyBox(xyxy=(5, 5, 10, 10), conf=0.8),
        # this box is near (100,100)-(200,200), center ~ (150,150), inside the ROI
        DummyBox(xyxy=(100, 100, 200, 200), conf=0.7),
    ]
    idx = select_lifter_index(boxes, orig_w=640, orig_h=640)
    # we expect the second box to be selected (index=1), since the first is out of ROI
    assert idx == 1

    # reset the ROI so it doesn't affect other tests
    mock_cfg["LIFTER_SELECTOR"]["roi"] = [0.0, 0.0, 1.0, 1.0]
