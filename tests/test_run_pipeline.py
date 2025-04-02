# tests/test_run_pipeline.py
"""
Test the run_pipeline function
usage: poetry run pytest tests/test_run_pipeline.py
"""
# import os
# import subprocess
# import time
# import webbrowser
# from pathlib import Path
# from typing import List
# import pytest
# from refvision.scripts.run_pipeline import local_pipeline
#
#
# def test_run_command(monkeypatch: pytest.MonkeyPatch) -> None:
#     """
#     test that run_command logs the command and calls subprocess.check_call.
#     :param monkeypatch: pytest fixture for mocking
#     :return: None
#     """
#     captured: List[str] = []
#
#     def fake_check_call(cmd_list: List[str]) -> None:
#         """
#         Fake check_call function that captures the command.
#         :param cmd_list: List of command arguments
#         :return: None
#         """
#         captured.append(" ".join(cmd_list))
#
#     monkeypatch.setattr(subprocess, "check_call", fake_check_call)
#     cmd = ["echo", "hello"]
#     local_pipeline.run_command(cmd)
#     assert "echo hello" in captured[0]
#
#
# def test_normalize_video(monkeypatch: pytest.MonkeyPatch) -> None:
#     """
#     Test that normalize_video constructs the proper ffmpeg command
#     :param monkeypatch: pytest fixture for mocking
#     :return: None
#     """
#     commands: List[List[str]] = []
#
#     def fake_run_command(cmd_list: List[str]) -> None:
#         """
#         Fake run_command function that captures the command.
#         :param cmd_list: List of command arguments
#         :return: None
#         """
#         commands.append(cmd_list)
#
#     monkeypatch.setattr(local_pipeline, "run_command", fake_run_command)
#     input_video = "input.mov"
#     output_video = "output.mp4"
#     local_pipeline.normalize_video(input_video, output_video)
#     # Verify the command includes expected parameters.
#     cmd = commands[0]
#     assert cmd[0] == "ffmpeg"
#     assert "-i" in cmd
#     assert input_video in cmd
#     assert output_video in cmd
#
#
# def test_run_yolo_inference(monkeypatch: pytest.MonkeyPatch) -> None:
#     """
#     Test that run_yolo_inference constructs the proper command.
#     :param monkeypatch: Pytest fixture for mocking.
#     :return: None
#     """
#     commands: List[List[str]] = []
#
#     def fake_run_command(cmd_list: List[str]) -> None:
#         """
#         Fake run_command function that captures the command.
#         :param cmd_list: List of command arguments
#         :return: None
#         """
#         commands.append(cmd_list)
#
#     monkeypatch.setattr(local_pipeline, "run_command", fake_run_command)
#     video = "video.mp4"
#     model_path = "model.pt"
#     local_pipeline.run_yolo_inference(video, model_path)
#     cmd = commands[0]
#     assert "poetry" in cmd[0]
#     assert "refvision.inference.inference" in cmd
#
#
# def test_convert_avi_to_mp4(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
#     """
#     Test that convert_avi_to_mp4 calls run_command and removes the AVI file
#     :param monkeypatch: pytest fixture for mocking
#     :param tmp_path: pytest fixture for temporary directory
#     :return: None
#     """
#     avi_file = tmp_path / "input.avi"
#     mp4_file = tmp_path / "output.mp4"
#     avi_file.write_text("dummy avi content")
#     commands: List[List[str]] = []
#
#     def fake_run_command(cmd_list: List[str]) -> None:
#         """
#         Fake run_command function that captures the command.
#         :param cmd_list: List of command arguments
#         :return: None
#         """
#         commands.append(cmd_list)
#
#     monkeypatch.setattr(local_pipeline, "run_command", fake_run_command)
#     local_pipeline.convert_avi_to_mp4(str(avi_file), str(mp4_file))
#     # verify the AVI file is removed.
#     assert not avi_file.exists()
#     # verify the command includes the mp4 output.
#     cmd = commands[0]
#     assert str(mp4_file) in cmd
#
#
# def test_convert_avi_to_mp4_file_not_found(tmp_path: Path) -> None:
#     """
#     test that convert_avi_to_mp4 exits if the AVI file is not found.
#     :param tmp_path: pytest fixture for temporary directory
#     :return: None
#     """
#     avi_file = tmp_path / "nonexistent.avi"
#     mp4_file = tmp_path / "output.mp4"
#     with pytest.raises(SystemExit):
#         local_pipeline.convert_avi_to_mp4(str(avi_file), str(mp4_file))
#
#
# def test_upload_video_to_s3(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
#     """
#     Test that upload_video_to_s3 uses get_s3_client to upload the file and
#     removes it
#     :param monkeypatch: pytest fixture for mocking
#     :param tmp_path: pytest fixture for temporary directory
#     :return: None
#     """
#     mp4_file = tmp_path / "video.mp4"
#     mp4_file.write_text("dummy mp4")
#
#     class DummyS3Client:
#         """
#         create a fake S3 client with an upload_fileobj method.
#         """
#
#         def __init__(self):
#             self.uploaded = False
#
#         def upload_fileobj(self, f, bucket, key, ExtraArgs):
#             """
#             upload_fileobj method that records the upload
#             :param f:
#             :param bucket:
#             :param key:
#             :param ExtraArgs:
#             :return:
#             """
#             self.uploaded = True
#             self.bucket = bucket
#             self.key = key
#
#     dummy_s3 = DummyS3Client()
#     monkeypatch.setattr(local_pipeline, "get_s3_client", lambda: dummy_s3)
#
#     # override os.remove to record removal.
#     removed_files: List[str] = []
#
#     def fake_remove(path: str) -> None:
#         """
#         fake_remove function that records the file path.
#         :param path: path to the file
#         :return: None
#         """
#         removed_files.append(path)
#
#     monkeypatch.setattr(os, "remove", fake_remove)
#
#     local_pipeline.upload_video_to_s3(str(mp4_file), "bucket", "key")
#     assert dummy_s3.uploaded
#     # assert str(mp4_file) in removed_files
#
#
# def test_launch_gunicorn(monkeypatch: pytest.MonkeyPatch) -> None:
#     """
#     Test that launch_gunicorn spawns a subprocess and opens a browser
#     :param monkeypatch: pytest fixture for mocking
#     :return: None
#     """
#     processes: List[List[str]] = []
#
#     class DummyProcess:
#         """
#         Fake process class that does nothing
#         """
#
#         def wait(self) -> None:
#             return
#
#     def fake_popen(cmd: List[str]):
#         """
#         fake_popen function that records the command.
#         :param cmd:
#         :return:
#         """
#         processes.append(cmd)
#         return DummyProcess()
#
#     monkeypatch.setattr(subprocess, "Popen", fake_popen)
#
#     opened_urls: List[str] = []
#
#     monkeypatch.setattr(webbrowser, "open", lambda url: opened_urls.append(url))
#
#     monkeypatch.setattr(time, "sleep", lambda x: None)
#
#     local_pipeline.launch_gunicorn("5000")
#     assert processes
#     assert any("0.0.0.0:5000" in " ".join(process) for process in processes)
#     assert "http://127.0.0.1:5000" in opened_urls
