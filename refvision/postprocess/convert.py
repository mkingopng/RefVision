# refvision/postprocess/convert.py
"""
Module for normalizing or converting video formats (e.g., .mov -> .mp4, .avi -> .mp4).
"""
import os
import subprocess
from typing import List


def run_command(cmd_list: List[str], logger=None) -> None:
    """
    Runs a command in a subprocess, optionally logging it.

    :param cmd_list: List of command arguments
    :param logger: (Optional) Logger for logging the command
    :return: None
    """
    if logger:
        logger.info(f"Running command: {' '.join(cmd_list)}")
    subprocess.check_call(cmd_list)


def normalize_video(input_video: str, output_dir: str, logger=None) -> str:
    """
    Converts input_video (any format) to a normalized .mp4 in output_dir,
    stripping metadata.

    :param input_video: Path to the input video file (mov, avi, etc.)
    :param output_dir: Directory to save the normalized .mp4 file
    :param logger: (Optional) Logger for logging progress
    :return: Path to the normalized .mp4 file
    """
    if logger:
        logger.info("=== Pre-step: Normalize input to MP4 ===")
    base_name = os.path.splitext(os.path.basename(input_video))[0]
    normalized_path = os.path.join(output_dir, f"{base_name}.mp4")

    cmd: List[str] = [
        "ffmpeg",
        "-y",
        "-i",
        input_video,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-map_metadata",
        "-1",
        normalized_path,
    ]
    run_command(cmd, logger=logger)
    return normalized_path


def convert_avi_to_mp4(avi_output: str, mp4_output: str, logger=None) -> None:
    """
    Converts a .avi file to .mp4 and removes the .avi file.
    :param avi_output: Path to the AVI file
    :param mp4_output: Path to the output MP4 file
    :param logger: (Optional) Logger for logging progress
    :return: None
    :raises FileNotFoundError: If the avi_output file does not exist.
    """
    if logger:
        logger.info("=== Convert AVI to MP4 ===")
    if not os.path.exists(avi_output):
        msg = f"ERROR: Expected AVI file '{avi_output}' not found"
        if logger:
            logger.error(msg)
        raise FileNotFoundError(msg)

    cmd: List[str] = [
        "ffmpeg",
        "-y",
        "-i",
        avi_output,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        mp4_output,
    ]
    run_command(cmd, logger=logger)
    os.remove(avi_output)
