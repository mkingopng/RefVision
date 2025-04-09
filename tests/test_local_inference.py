# tests/test_local_inference.py
"""
Tests for local_inference.py
"""

import sys
import pytest
from unittest.mock import patch, MagicMock, ANY
from refvision.inference.local_inference import parse_args, run_inference


def test_parse_args_required_video():
    """
    parse_args() should fail if we don't provide --video.
    We'll patch sys.argv to simulate command line usage.
    """
    test_argv = [
        "script_name",
        "--model_path",
        "./model_zoo/yolo11x-pose.pt",
        "--athlete_id",
        "1234",
        "--record_id",
        "some_record",
    ]
    with patch.object(sys, "argv", test_argv):
        with pytest.raises(SystemExit):
            parse_args()


def test_parse_args_ok():
    """
    parse_args() with valid arguments returns a namespace
    containing 'video', 'model_path', 'athlete_id', and 'record_id'.
    """
    test_argv = [
        "script_name",
        "--video",
        "my_video.mp4",
        "--model_path",
        "some_model_path.pt",
        "--athlete_id",
        "1234",
        "--record_id",
        "some_record",
    ]
    with patch.object(sys, "argv", test_argv):
        args = parse_args()
        assert args.video == "my_video.mp4"
        assert args.model_path == "some_model_path.pt"
        assert args.athlete_id == "1234"
        assert args.record_id == "some_record"


@pytest.fixture
def mock_sys_exit():
    """
    A fixture that patches sys.exit to raise a RuntimeError instead
    of killing the test process.
    """
    with patch("sys.exit", side_effect=RuntimeError("sys.exit called")) as mock_exit:
        yield mock_exit


def test_run_inference_missing_video(mock_sys_exit, caplog):
    fake_args = MagicMock()
    fake_args.video = "nonexistent.mp4"
    fake_args.model_path = "whatever.pt"
    fake_args.athlete_id = "1234"
    fake_args.record_id = "some_record"

    def mock_exists(path):
        if path == "whatever.pt":
            return True
        elif path == "nonexistent.mp4":
            return False
        return True

    with patch(
        "refvision.inference.local_inference.os.path.exists", side_effect=mock_exists
    ):
        with pytest.raises(RuntimeError, match="sys.exit called"):
            run_inference(
                video_file=fake_args.video,
                model_path=fake_args.model_path,
                athlete_id=fake_args.athlete_id,
                record_id=fake_args.record_id,
            )

    assert "Error: Video file nonexistent.mp4 does not exist." in caplog.text


def test_run_inference_success(tmp_path, caplog):
    """
    If the video file exists, run_inference should:
      1) load the model
      2) run model.track(...)
      3) call check_squat_depth_by_turnaround
      4) not call sys.exit
    """
    video_path = tmp_path / "fake_video.mp4"
    video_path.touch()

    fake_args = MagicMock()
    fake_args.video = str(video_path)
    fake_args.model_path = "fake_model_path.pt"
    fake_args.athlete_id = "1234"
    fake_args.record_id = "some_record"

    fake_frame = MagicMock()
    fake_frame.boxes = []
    fake_frame.keypoints = []
    mock_frame_generator = [fake_frame, fake_frame]

    mock_model = MagicMock()
    mock_model.track.return_value = mock_frame_generator

    with patch(
        "refvision.inference.local_inference.parse_args", return_value=fake_args
    ), patch(
        "refvision.inference.local_inference.os.path.exists", return_value=True
    ), patch(
        "refvision.inference.local_inference.load_model",
        return_value=(mock_model, "cpu"),
    ), patch(
        "refvision.inference.local_inference.check_squat_depth_by_turnaround",
        return_value={"decision": "Good Lift!"},
    ):
        run_inference(
            video_file=fake_args.video,
            model_path=fake_args.model_path,
            athlete_id=fake_args.athlete_id,
            record_id=fake_args.record_id,
        )

        assert "error" not in caplog.text.lower()
        mock_model.track.assert_called_once_with(
            source=str(video_path),
            device="cpu",
            show=False,
            save=True,
            project=ANY,
            exist_ok=True,
            max_det=1,
            batch=128,
        )
        assert "Final decision => {'decision': 'Good Lift!'}" in caplog.text
