# tests/test_lifter_selector.py
"""
Tests for the lifter_selector module
"""
from typing import Optional, List, Any
from refvision.inference.lifter_selector import select_lifter_index
import refvision.inference.lifter_selector as ls_mod


class DummyBox:
    """
    Fake class to simulate a detection box.
    """

    def __init__(self, xyxy: Any, conf: float, id: Optional[int] = None) -> None:
        self.xyxy = [xyxy]
        self.conf = conf
        self.id = id


class DummyCFG:
    """
    Fake configuration class to simulate CFG.lifter_selector
    """

    lifter_selector = {
        "expected_center": [0.5, 0.5],
        "roi": [0.0, 0.0, 1.0, 1.0],
        "distance_weight": 1.0,
        "confidence_weight": 1.0,
        "lifter_id": None,
    }


dummy_cfg = DummyCFG()
ls_mod.Config.LIFTER_SELECTOR = dummy_cfg.lifter_selector


def test_select_lifter_index_basic() -> None:
    """
    Test the basic functionality of select_lifter_index
    :return: None
    """
    boxes: List[DummyBox] = [
        DummyBox(xyxy=(0, 0, 10, 10), conf=0.8),
        DummyBox(xyxy=(30, 30, 40, 40), conf=0.9),
    ]
    # With default configuration, the box with higher score (closer to center) is chosen.
    idx = select_lifter_index(boxes, 640, 640)
    assert idx == 1


def test_select_lifter_index_with_lifter_id() -> None:
    """
    Test the select_lifter_index function with a specified lifter_id
    :return: None
    """
    DummyCFG.lifter_selector["lifter_id"] = 42
    boxes: List[DummyBox] = [
        DummyBox(xyxy=(0, 0, 10, 10), conf=0.8, id=1),
        DummyBox(xyxy=(30, 30, 40, 40), conf=0.9, id=42),
    ]
    idx = select_lifter_index(boxes, 640, 640)
    assert idx == 1
    DummyCFG.lifter_selector["lifter_id"] = None  # Reset for other tests.


def test_select_lifter_index_roi() -> None:
    """
    Test the select_lifter_index function with a specified ROI
    :return: None
    """
    DummyCFG.lifter_selector["roi"] = [0.1, 0.1, 0.9, 0.9]
    # First box is outside the ROI, second is inside.
    boxes: List[DummyBox] = [
        DummyBox(xyxy=(0, 0, 10, 10), conf=0.8),
        DummyBox(xyxy=(100, 100, 200, 200), conf=0.7),
    ]
    idx = select_lifter_index(boxes, 640, 640)
    # ROI in pixels: (64, 64) to (576, 576) so the second box qualifies.
    assert idx == 1
    DummyCFG.lifter_selector["roi"] = [0.0, 0.0, 1.0, 1.0]
