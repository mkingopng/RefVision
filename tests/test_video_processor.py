# tests/test_video_processor.py
"""

"""
# import os
# import cv2
# import numpy as np
# from typing import Any, Dict
# from pathlib import Path
# from refvision.inference import video_processor
#
#
# # Dummy classes to simulate inference results.
# class DummyKeypoints:
#     def __init__(self, xy):
#         self.xy = xy
#
#
# class DummyBox:
#     def __init__(self, xyxy, conf, id=None):
#         self.xyxy = [xyxy]
#         self.conf = conf
#         self.id = id
#
#
# class DummyFrameResult:
#     def __init__(self, keypoints, boxes):
#         self.keypoints = keypoints
#         self.boxes = boxes
#
#
# def create_dummy_video(tmp_path: Path) -> str:
#     """
#     Creates a one-frame dummy video and returns its path.
#     """
#     video_path = str(tmp_path / "test_video.mp4")
#     fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore[attr-defined]
#     writer = cv2.VideoWriter(video_path, fourcc, 1.0, (100, 100))
#     frame = np.zeros((100, 100, 3), dtype=np.uint8)
#     writer.write(frame)
#     writer.release()
#     return video_path
#
#
# def test_annotate_video(tmp_path: Path) -> None:
#     """
#     Test that annotate_video creates an output file.
#     """
#     video_file = create_dummy_video(tmp_path)
#     # Create a dummy inference result with one frame, one detection.
#     dummy_kpts = DummyKeypoints(xy=np.array([[50, 50]]))
#     dummy_box = DummyBox(xyxy=(40, 40, 60, 60), conf=0.9)
#     dummy_result = DummyFrameResult(keypoints=[dummy_kpts], boxes=[dummy_box])
#     results = [dummy_result]
#     config: Dict[str, Any] = {"lifter_selector": {"excluded_ids": []}}
#     out_path = video_processor.annotate_video(video_file, results, config)
#     assert os.path.exists(out_path)
#     # Check that the file is not empty.
#     assert os.path.getsize(out_path) > 0
