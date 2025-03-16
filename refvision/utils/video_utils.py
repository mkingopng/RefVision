# refvision/utils/video_utils.py
"""
this utility module will help load frames from a video file.
"""
import cv2
import logging

logger = logging.getLogger(__name__)


def load_video_frames(video_path: str, resize: tuple = (640, 640)) -> list:
    """
    Loads frames from a video file.

    :param video_path: Path to the video file.
    :param resize: Target size (width, height) for each frame.
    :return: List of frames as NumPy arrays.
    """
    logger.info(f"📥 Loading video frames from: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"❌ Failed to open video file: {video_path}")
        return []

    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break  # End of video

        # Resize frame
        frame = cv2.resize(frame, resize)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR → RGB
        frames.append(frame)

    cap.release()
    logger.info(f"✅ Loaded {len(frames)} frames from video.")
    return frames
