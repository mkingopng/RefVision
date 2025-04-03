# tests/test_find_turnaround_frame.py
"""
Tests for the turnaround detector.
"""
# import numpy as np
# from typing import Any, Optional
# from refvision.common.config_base import Config
# from refvision.analysis.find_turnaround_frame import find_turnaround_frame
# import refvision.inference.lifter_selector as ls_mod
#
#
# class DummyCFG(Config):
#     """
#     Fake class to simulate the CFG class.
#     """
#
#     lifter_selector: dict[str, Any] = {
#         "expected_center": [0.5, 0.5],
#         "roi": [0.0, 0.0, 1.0, 1.0],
#         "distance_weight": 1.0,
#         "confidence_weight": 1.0,
#         "lifter_id": None,
#     }
#
#
# dummy_cfg = DummyCFG()
# ls_mod.Config.LIFTER_SELECTOR = dummy_cfg.lifter_selector
#
#
# class DummyKeypoints:
#     """
#     Fake class to simulate key points.
#     """
#
#     def __init__(self, xy: np.ndarray) -> None:
#         self.xy = xy
#
#
# class DummyFrameResult:
#     """
#     Fake class to simulate frame results.
#     """
#
#     def __init__(self, keypoints: list, boxes: list, orig_shape=(640, 640)) -> None:
#         self.keypoints = keypoints
#         self.boxes = boxes
#         self.orig_shape = orig_shape
#
#
# class DummyBox:
#     """
#     Dummy class to simulate detection boxes.
#     """
#
#     def __init__(self, xyxy: Any, conf: float, id: Optional[dict] = None) -> None:
#         self.xyxy = [xyxy]
#         self.conf = conf
#         self.id = id
#
#
# def create_dummy_frame(avg_hip_y: float) -> DummyFrameResult:
#     """
#     Create a fake frame result with a given average hip y-coordinate
#     :param avg_hip_y: average hip y-coordinate
#     :return: fake frame result
#     """
#     # create a fake key points array with shape (17, 2)
#     kpts_arr = np.zeros((17, 2), dtype=float)
#     # set both hip key points.
#     kpts_arr[11, 1] = avg_hip_y
#     kpts_arr[12, 1] = avg_hip_y
#     keypoints = [DummyKeypoints(xy=kpts_arr)]
#     boxes = [DummyBox(xyxy=(0, 0, 10, 10), conf=0.9)]
#     return DummyFrameResult(keypoints=keypoints, boxes=boxes)
#
#
# def test_find_turnaround_frame() -> None:
#     """
#     Test that find_turnaround_frame selects the frame with the highest average
#     hip y
#     :return: None
#     """
#     # create three frames with different hip positions.
#     frames = [create_dummy_frame(avg) for avg in [100, 200, 150]]
#     idx = find_turnaround_frame(frames)
#     # highest average hip y is 200 at index 1.
#     assert idx == 1
#
#
# def test_find_turnaround_frame_with_invalid_frames() -> None:
#     """
#     Test that find_turnaround_frame correctly skips invalid frames.
#     :return: None
#     """
#     # create one frame with no key points/boxes and another valid frame.
#     frames = [DummyFrameResult(keypoints=[], boxes=[]), create_dummy_frame(300)]
#     idx = find_turnaround_frame(frames)
#     assert idx == 1  # only second frame is valid
