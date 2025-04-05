# tests/test_local_inference.py
"""
Tests for local_inference.py
"""

import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open, ANY
from refvision.inference.local_inference import parse_args, run_inference


def test_parse_args_required_video():
    """
    parse_args() should fail if we don't provide --video.
    We'll patch sys.argv to simulate command line usage.
    """
    test_argv = ["script_name", "--model_path", "./model_zoo/yolo11x-pose.pt"]
    with patch.object(sys, "argv", test_argv):
        with pytest.raises(SystemExit):
            parse_args()


def test_parse_args_ok():
    """
    parse_args() with valid arguments returns a namespace
    containing 'video' and 'model_path'.
    """
    test_argv = [
        "script_name",
        "--video",
        "my_video.mp4",
        "--model_path",
        "some_model_path.pt",
    ]
    with patch.object(sys, "argv", test_argv):
        args = parse_args()
        assert args.video == "my_video.mp4"
        assert args.model_path == "some_model_path.pt"


@pytest.fixture
def mock_sys_exit():
    """
    A fixture that patches sys.exit to raise a RuntimeError instead
    of killing the test process.
    """
    with patch("sys.exit", side_effect=RuntimeError("sys.exit called")) as mock_exit:
        yield mock_exit


def test_run_inference_missing_video(mock_sys_exit, caplog):
    """
    If the video file doesn't exist, run_inference() should log an error
    and call sys.exit(1). We'll patch os.path.exists to differentiate
    between the model path and the video path, so the model path
    doesn't raise FileNotFoundError first.
    """
    fake_args = MagicMock()
    fake_args.video = "nonexistent.mp4"
    fake_args.model_path = "whatever.pt"

    def mock_exists(path):
        # If the path is the model file, pretend it exists:
        if path == "whatever.pt":
            return True
        # If the path is the missing video, return False:
        elif path == "nonexistent.mp4":
            return False
        # For anything else, default True:
        return True

    with patch(
        "refvision.inference.local_inference.parse_args", return_value=fake_args
    ), patch(
        "refvision.inference.local_inference.os.path.exists", side_effect=mock_exists
    ):

        # sys.exit(1) is replaced by a RuntimeError("sys.exit called")
        with pytest.raises(RuntimeError, match="sys.exit called"):
            run_inference()

    # Confirm the code logs an error about missing video
    assert "Error: Video file nonexistent.mp4 does not exist." in caplog.text


def test_run_inference_success(tmp_path, caplog):
    """
    If the video file exists, run_inference should:
      1) load the model
      2) run model.track(...)
      3) call check_squat_depth_by_turnaround
      4) write the decision to inference_results.json
      5) not call sys.exit
    """
    # We'll create a dummy "video" path
    video_path = tmp_path / "fake_video.mp4"
    video_path.touch()  # an empty file

    # Fake parse_args return
    fake_args = MagicMock()
    fake_args.video = str(video_path)
    fake_args.model_path = "fake_model_path.pt"

    # Mock model.track to yield a few "frames"
    fake_frame = MagicMock()
    fake_frame.boxes = []
    fake_frame.keypoints = []
    mock_frame_generator = [fake_frame, fake_frame]

    # Mock model object
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
    ), patch(
        "builtins.open", mock_open()
    ) as mock_file:

        run_inference()

        # Ensure no error was logged about missing video
        assert (
            "error" not in caplog.text.lower()
        ), "Should not log error about missing video"

        # Check model.track was called with the correct arguments
        mock_model.track.assert_called_once_with(
            source=str(video_path),
            device="cpu",
            show=False,
            save=True,
            project=ANY,  # from cfg["OUTPUT_DIR"]
            exist_ok=True,
            max_det=1,
            batch=128,
        )

        # Confirm the code wrote the JSON decision file
        # Because json.dump might chunk up the writes, gather them all
        write_file_handle = mock_file()
        written_chunks = [
            call.args[0] for call in write_file_handle.write.call_args_list
        ]
        all_written = "".join(written_chunks)

        # Check that the final content includes our JSON data
        assert '{"decision": "Good Lift!"}' in all_written, f"Got: {all_written}"

        # Also confirm the logs show the final decision
        assert "Final decision +> {'decision': 'Good Lift!'}" in caplog.text
