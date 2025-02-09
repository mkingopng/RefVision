# config.py
"""
Global configuration for RefVision pipeline.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # config directory

class CFG:
    VIDEO = os.path.join(BASE_DIR, "..", "data", "raw_data", "chris_kennedy_squat_1.mp4")
    MODEL_PATH = os.path.join(BASE_DIR, "..", "model_zoo", "yolo11x-pose.pt")
    AVI_OUTPUT = os.path.join(BASE_DIR, "..", "runs", "pose", "track", "chris_kennedy_squat_1.avi")
    MP4_OUTPUT = os.path.join(BASE_DIR, "..", "runs", "pose", "track", "chris_kennedy_squat_1.mp4")
    MP4_FILE = os.path.join(BASE_DIR, "..", "temp_videos", "chris_kennedy_squat_1.mp4")
    S3_BUCKET = "refvision-annotated-videos"
    S3_KEY = "chris_kennedy_squat_1.mp4"
    FLASK_PORT = 5000
    LIFTER_ID = 5
