# config.py
"""
Global configuration for RefVision pipeline.
"""

class CFG:
	"""
	configuration class holding default paths and settings.
	"""
	video = "data/raw_data/jessica_good_lift.MOV"
	model_path = "./model_zoo/yolo11x-pose.pt"
	avi_output = "runs/pose/track/jessica_good_lift.avi"
	mp4_output = "runs/pose/track/jessica_good_lift.mp4"
	mp4_file = "jessica_good_lift.mp4"
	s3_bucket = "refvision-annotated-videos"
	s3_key = "jessica_good_lift.mp4"
	flask_port = 5000
