# config.py
"""
Global configuration for RefVision pipeline.
"""

class CFG:
	"""
	Configuration class holding default paths and settings.
	"""
	video = "data/raw_data/thomas_high.MOV"
	model_path = "./model_zoo/yolo11x-pose.pt"
	avi_output = "runs/pose/track/thomas_high.avi"
	mp4_output = "runs/pose/track/thomas_high.mp4"
	mp4_file = "thomas_high.mp4"
	s3_bucket = "refvision-annotated-videos"
	s3_key = "thomas_high.mp4"
	flask_port = 5000
