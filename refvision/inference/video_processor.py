# refvision/inference/model_loader.py
"""
Module for processing video and annotating frames with skeleton overlays.
"""
import os
import cv2
import numpy as np
from typing import Any, List
import logging
from refvision.analysis.lifter_selector import select_lifter_index


logger = logging.getLogger(__name__)


def annotate_video(video_file: str, results: List[Any], config: dict) -> str:
    """
    Annotates the given video with skeleton overlays from inference results.
    :param video_file: (str) Path to the input video.
    :param results: (List[Any]) Inference results for each frame.
    :param config: (dict) Configuration dictionary.
    :returns: (str) Path to the annotated video.
    :raises: RuntimeError If the video file cannot be opened.
    """
    cap = cv2.VideoCapture(video_file)
    if not cap.isOpened():
        logger.error("Could not open video file.")
        raise RuntimeError("Could not open video file.")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore[attr-defined]
    out_path = os.path.join("tmp", "annotated_output.mp4")
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    os.makedirs("tmp", exist_ok=True)
    writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    excluded_ids = config.get("lifter_selector", {}).get("excluded_ids", [])

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx < len(results):
            frame_result = results[frame_idx]
            if frame_result.keypoints and frame_result.boxes:
                lifter_idx = select_lifter_index(frame_result.boxes, width, height)
                if lifter_idx is not None:
                    box = frame_result.boxes[lifter_idx]
                    box_id = getattr(box, "stack_id", None)
                    if box_id is not None and box_id in excluded_ids:
                        logger.debug(
                            f"Skipping skeleton overlay for detection with stack_id {box_id}."
                        )
                    else:
                        kpts = frame_result.keypoints[lifter_idx]
                        if len(kpts.xy.shape) == 3 and kpts.xy.shape[0] == 1:
                            kpts_xy = kpts.xy.squeeze(0)
                        else:
                            kpts_xy = kpts.xy
                        keypoints = np.array(
                            kpts_xy.cpu() if hasattr(kpts_xy, "cpu") else kpts_xy
                        )
                        for x, y in keypoints:
                            cv2.circle(frame, (int(x), int(y)), 4, (0, 255, 0), -1)
        writer.write(frame)
        frame_idx += 1

    cap.release()
    writer.release()
    logger.info(f"Annotated video saved to {out_path}")
    return out_path
