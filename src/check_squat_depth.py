# src/check_squat_depth.py

import torch
import numpy as np

LEFT_HIP_IDX = 11
RIGHT_HIP_IDX = 12
LEFT_KNEE_IDX = 13
RIGHT_KNEE_IDX = 14

def check_squat_depth(results, threshold=0.0):
    """
    Scans all frames in 'results' to find the frame where the lifter's hips
    are at their lowest relative to the knees (i.e., largest (hipY - kneeY)).
    - If no frames or no detections are found, returns "FAIL."
    - If best (hipY - kneeY) is above 'threshold', returns "PASS."
    """

    if not results:
        return "FAIL"

    best_frame_idx = None
    best_delta = float('-inf')

    for f_idx, frame_result in enumerate(results):
        # skip if no keypoints or no bounding boxes
        if not frame_result.keypoints or not frame_result.boxes:
            continue

        kpts = frame_result.keypoints
        boxes = frame_result.boxes

        if hasattr(frame_result, 'orig_shape') and frame_result.orig_shape:
            orig_h, orig_w = frame_result.orig_shape
        else:
            orig_h, orig_w = 640, 640

        center_x_img = orig_w / 2
        center_y_img = orig_h / 2

        lifter_idx = None
        min_dist_sq = float('inf')

        for i, box in enumerate(boxes):
            xyxy = box.xyxy[0]
            x1, y1, x2, y2 = xyxy
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            dist_sq = (cx - center_x_img)**2 + (cy - center_y_img)**2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                lifter_idx = i

        if lifter_idx is None:
            # no bounding box for the lifter?
            continue

        lifter_kps = kpts[lifter_idx]
        # Check if we even have the indices we need:
        if lifter_kps.xy.shape[0] <= RIGHT_KNEE_IDX:
            # i.e. fewer than 15 total keypoints, skip
            continue

        left_hip_y = lifter_kps.xy[LEFT_HIP_IDX, 1].item()
        right_hip_y = lifter_kps.xy[RIGHT_HIP_IDX, 1].item()
        left_knee_y = lifter_kps.xy[LEFT_KNEE_IDX, 1].item()
        right_knee_y = lifter_kps.xy[RIGHT_KNEE_IDX, 1].item()

        avg_hip_y = (left_hip_y + right_hip_y) / 2.0
        avg_knee_y = (left_knee_y + right_knee_y) / 2.0
        delta = avg_hip_y - avg_knee_y

        if delta > best_delta:
            best_delta = delta
            best_frame_idx = f_idx

    if best_frame_idx is None:
        # never found a valid frame
        return "FAIL"

    if best_delta > threshold:
        return "PASS"
    else:
        return "FAIL"
