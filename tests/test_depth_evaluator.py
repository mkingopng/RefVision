# tests/test_depth_evaluator.py
"""
Tests for the depth_evaluator module functions
"""
import os
from pathlib import Path
from typing import Any, List
import pytest
from refvision.inference import depth_evaluator


def dummy_check_squat_depth_by_turnaround(results: List[Any]) -> str:
    """
    Dummy function to simulate check_squat_depth_by_turnaround.
    :param results: (List[Any]) Dummy list of inference results.
    :returns str: A fixed decision string "Good Lift!".
    """
    return "Good Lift!"


def test_evaluate_depth(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test that evaluate_depth returns the expected decision.
    This test patches the check_squat_depth_by_turnaround function within
    depth_evaluator to return a dummy value, and then verifies that
    evaluate_depth propagates that decision correctly.
    :param monkeypatch: The pytest monkeypatch fixture.
    :return: None
    """
    dummy_results: List[Any] = []
    dummy_video = "dummy_video.mp4"
    monkeypatch.setattr(
        depth_evaluator,
        "check_squat_depth_by_turnaround",
        dummy_check_squat_depth_by_turnaround,
    )
    decision = depth_evaluator.evaluate_depth(dummy_results, dummy_video)
    assert decision == "Good Lift!"


def test_save_decision(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test that save_decision writes the decision to the expected file. This test
    overrides the os.path.join function used within the depth_evaluator module
    for the final file path (i.e. for "decision.txt") so that the file is
    written to the temporary directory provided by tmp_path. It then checks
    that the file exists and contains the correct content.
    :param tmp_path: (Path) A temporary directory provided by pytest.
    :param monkeypatch: The pytest monkeypatch fixture.
    :return: None
    """
    decision = "Good Lift!"
    original_join = os.path.join

    def fake_join(*args):
        """
                Fake os.path.join function that redirects the output file to the
                temporary directory.
        :param args: *args (str) Components of the path.
        :return: str: The joined path. If the last component is "decision.txt",
        returns a path within tmp_path.
        """
        if args and args[-1] == "decision.txt":
            return str(tmp_path / "decision.txt")
        return original_join(*args)

    monkeypatch.setattr("refvision.inference.depth_evaluator.os.path.join", fake_join)
    depth_evaluator.save_decision(decision)
    decision_path = tmp_path / "decision.txt"
    assert decision_path.exists(), f"{decision_path} does not exist"
    with open(decision_path, "r") as f:
        content = f.read()
    assert content == decision
