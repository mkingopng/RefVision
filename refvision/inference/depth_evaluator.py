# refvision/analysis/depth_checker.py
"""
Module for evaluating squat depth from inference results.
"""
import os
import logging
from typing import Any, List
from refvision.analysis.depth_checker import check_squat_depth_by_turnaround


logger = logging.getLogger(__name__)


def evaluate_depth(results: List[Any], video_file: str) -> str:
    """
    evaluates squat depth using the inference results
    :param results: (List[Any]) Inference results for each frame
    :param video_file: (str) Path to the video (for logging purposes)
    :returns: (str) The decision string ("Good Lift!" or "No Lift")
    """
    decision = check_squat_depth_by_turnaround(results)
    logger.info(f"Video: {video_file} => Decision: {decision}")
    return decision


def save_decision(decision: str) -> None:
    """
    saves the decision to a file in the tmp directory
    :param decision: (str) The decision string to save
    :returns: None
    """
    tmp_dir = os.path.join(os.path.dirname(__file__), "../../tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    decision_path = os.path.join(tmp_dir, "decision.txt")
    with open(decision_path, "w") as f:
        f.write(decision)
