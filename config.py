# config.py
"""
Global configuration for RefVision pipeline.
"""

class CFG:
	"""
	configuration class holding default paths and settings.
	"""
	VIDEO = "data/raw_data/chris_kennedy_squat_1.mp4"
	MODEL_PATH = "./model_zoo/yolo11x-pose.pt"
	AVI_OUTPUT = "runs/pose/track/chris_kennedy_squat_1.avi"
	MP4_OUTPUT = "runs/pose/track/chris_kennedy_squat_1.mp4"
	MP4_FILE = "chris_kennedy_squat_1.mp4"
	S3_BUCKET = "refvision-annotated-videos"
	S3_KEY = "chris_kennedy_squat_1.mp4"
	FLASK_PORT = 5000
	LIFTER_ID = 5
