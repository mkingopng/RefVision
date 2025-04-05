# tests/test_run_pipeline.py
"""
Tests for refvision/scripts/run_pipeline.py
Only tests the functions truly defined in run_pipeline.py:
    1) run_yolo_inference
    2) local_pipeline (smoke/integration-style test)
"""

# import pytest
# from typing import List
# from refvision.scripts.run_pipeline import run_yolo_inference
#
#
# def test_run_yolo_inference(monkeypatch: pytest.MonkeyPatch) -> None:
#     """
#     Check that run_yolo_inference() constructs the correct command
#     and calls run_command (which is imported from refvision.postprocess.convert).
#     We'll monkeypatch that imported run_command function so we can inspect the commands.
#     """
#     captured_cmds: List[List[str]] = []
#
#     def fake_run_command(cmd_list: List[str]) -> None:
#         captured_cmds.append(cmd_list)
#
#     monkeypatch.setattr("refvision.scripts.run_pipeline.run_command", fake_run_command)
#
#     video = "some_video.mp4"
#     model_path = "model.pt"
#
#     run_yolo_inference(video, model_path)
#
#     assert (
#         len(captured_cmds) == 1
#     ), "run_yolo_inference should call run_command exactly once"
#     cmd = captured_cmds[0]
#     assert "poetry" in cmd[0], "Expected 'poetry' at the start"
#     assert (
#         "refvision.inference.inference" in cmd
#     ), "Expected to run the 'refvision.inference.inference' module"
#     assert video in cmd, "Video file should be in the command arguments"
#     assert model_path in cmd, "Model path should be in the command arguments"
#
#
# def test_local_pipeline_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
#     """
#     A simple 'smoke test' for local_pipeline().
#     We'll skip real ffmpeg, real S3, and real Dynamo by monkeypatching them.
#     """
#
#     import sys
#     from refvision.scripts.run_pipeline import local_pipeline
#
#     # 1) Monkeypatch the heavy calls that fail in local dev
#     def fake_download_file_from_s3(bucket, key, local_path, logger=None):
#         pass  # do nothing
#
#     def fake_upload_file_to_s3(
#         local_path, bucket, key, content_type="video/mp4", logger=None
#     ):
#         pass  # do nothing
#
#     def fake_normalize_video(input_video, output_dir, logger=None):
#         # Return a dummy path instead of calling ffmpeg
#         return "/fake/path/normalized.mp4"
#
#     def fake_run_yolo_inference(video, model_path):
#         pass  # do nothing
#
#     def fake_convert_avi_to_mp4(avi_output, mp4_output, logger=None):
#         pass  # do nothing
#
#     def fake_launch_gunicorn(port, logger=None):
#         pass  # do nothing
#
#     def fake_os_remove(path: str):
#         pass  # do nothing
#
#     def fake_handle_error(meet_id, record_id, error, lifter_name=None, status="FAILED"):
#         # If you want to skip the actual Dynamo call
#         raise SystemExit("handle_error was called, pipeline failed unexpectedly.")
#
#     # Monkeypatch references in run_pipeline.py
#     monkeypatch.setattr(
#         "refvision.scripts.run_pipeline.download_file_from_s3",
#         fake_download_file_from_s3,
#     )
#     monkeypatch.setattr(
#         "refvision.scripts.run_pipeline.upload_file_to_s3", fake_upload_file_to_s3
#     )
#     monkeypatch.setattr(
#         "refvision.scripts.run_pipeline.normalize_video", fake_normalize_video
#     )
#     monkeypatch.setattr(
#         "refvision.scripts.run_pipeline.run_yolo_inference", fake_run_yolo_inference
#     )
#     monkeypatch.setattr(
#         "refvision.scripts.run_pipeline.convert_avi_to_mp4", fake_convert_avi_to_mp4
#     )
#     monkeypatch.setattr(
#         "refvision.scripts.run_pipeline.launch_gunicorn", fake_launch_gunicorn
#     )
#     monkeypatch.setattr("os.remove", fake_os_remove)
#     monkeypatch.setattr(
#         "refvision.scripts.run_pipeline.handle_error", fake_handle_error
#     )
#
#     # 2) Supply fake CLI args so argparse sees them
#     orig_argv = sys.argv
#     try:
#         sys.argv = [
#             "run_pipeline.py",
#             "--raw-bucket",
#             "my_fake_bucket",
#             "--raw-key",
#             "some_video.mov",
#             "--model-path",
#             "model.pt",
#             "--flask-port",
#             "9999",
#         ]
#         # 3) Just call local_pipeline() and confirm it doesn't call handle_error
#         local_pipeline()
#     except SystemExit as e:
#         # If handle_error is triggered, we raise SystemExit with a message
#         pytest.fail(f"Pipeline unexpectedly failed with error: {e}")
#     finally:
#         sys.argv = orig_argv
