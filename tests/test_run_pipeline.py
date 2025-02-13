# tests/test_run_pipeline.py
"""
Test the run_pipeline function
usage: poetry run pytest tests/test_run_pipeline.py
"""
import os
import subprocess
import pytest
from scripts.run_pipeline import run_command, normalize_video


def fake_check_call(cmd_list):
    """
    Fake call to check_call
    :param cmd_list:
    :return:
    """
    print("Fake call:", " ".join(cmd_list))
    return


def test_run_command(monkeypatch):
    """
    Test the run_command function
    :param monkeypatch:
    :return:
    """
    monkeypatch.setattr(subprocess, "check_call", fake_check_call)
    run_command(["echo", "hello"])


def test_normalize_video(monkeypatch, tmp_path):
    """
    Test the normalize_video function
    :param monkeypatch:
    :param tmp_path:
    :return:
    """
    # Create a dummy input file.
    dummy_input = tmp_path / "input.mp4"
    dummy_input.write_bytes(b"dummy data")
    dummy_output = tmp_path / "output.mp4"
    monkeypatch.setattr(subprocess, "check_call", fake_check_call)
    normalize_video(str(dummy_input), str(dummy_output))