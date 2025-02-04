# src/check_squat_depth.py
"""
detect squat depth
"""
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
    Instead of picking a detection by largest bounding box or highest confidence,
    we pick the detection whose bounding box center is closest to the image center.

    - If no frames or no detections are found, returns "FAIL."
    - If the best (hipY - kneeY) is above 'threshold', returns "PASS."
      Typically threshold=0 means "hip below knee" if hipY > kneeY.
    """

    if not results:
        return "FAIL"

    best_frame_idx = None
    best_delta = float('-inf')  # track the largest (hipY - kneeY)

    for f_idx, frame_result in enumerate(results):
        boxes = frame_result.boxes
        kpts = frame_result.keypoints

        # skip if no boxes or no keypoints
        if not boxes or not kpts:
            continue

        # The 'orig_shape' in frame_result may help find image center
        # but if not available, assume 640x640 or read from boxes
        if hasattr(frame_result, 'orig_shape') and frame_result.orig_shape:
            orig_h, orig_w = frame_result.orig_shape
        else:
            # fallback guess
            orig_h, orig_w = 640, 640

        # image center
        center_x_img = orig_w / 2
        center_y_img = orig_h / 2

        # ------------------------------------------
        # Pick the detection whose bounding box center
        # is closest to (center_x_img, center_y_img)
        # ------------------------------------------
        lifter_idx = None
        min_dist_sq = float('inf')  # track squared distance

        for i, box in enumerate(boxes):
            # box.xyxy shape: (1,4) => [x1, y1, x2, y2]
            xyxy = box.xyxy[0]
            x1, y1, x2, y2 = xyxy
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2

            # squared distance to image center
            dx = (cx - center_x_img)
            dy = (cy - center_y_img)
            dist_sq = dx*dx + dy*dy

            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                lifter_idx = i

        if lifter_idx is None:
            continue

        # Now we retrieve that detection's keypoints using
        # the official Keypoints object methods
        # keypoints[lifter_idx].xy => shape: (17,2) [x,y]
        # keypoints[lifter_idx].conf => shape: (17,) for confidences
        # e.g. keypoints[lifter_idx].xy[LEFT_HIP_IDX, 1] => y of the left hip

        lifter_kps = kpts[lifter_idx]
        # lifter_kps.xy => (17,2)
        # lifter_kps.conf => (17,)  (we won't sum them here, but you could)

        # Extract the Y-coords of relevant joints
        left_hip_y  = lifter_kps.xy[LEFT_HIP_IDX, 1].item()  # .item() => float
        right_hip_y = lifter_kps.xy[RIGHT_HIP_IDX, 1].item()
        left_knee_y  = lifter_kps.xy[LEFT_KNEE_IDX, 1].item()
        right_knee_y = lifter_kps.xy[RIGHT_KNEE_IDX, 1].item()

        avg_hip_y  = (left_hip_y + right_hip_y) / 2.0
        avg_knee_y = (left_knee_y + right_knee_y) / 2.0

        delta = avg_hip_y - avg_knee_y  # "hip below knee" => hipY > kneeY

        if delta > best_delta:
            best_delta = delta
            best_frame_idx = f_idx

    # final pass/fail check
    if best_frame_idx is None:
        return "FAIL"

    if best_delta > threshold:
        return "PASS"
    else:
        return "FAIL"
