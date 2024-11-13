import os
from ultralytics import YOLO
import torch

# set device
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
print(f"Using device: {device}")

# load the model
model = YOLO('./model_zoo/yolo11x-pose')

# specify the directory containing the videos
video_dir = 'data/train/train_videos'

# get a list of all video files in the directory
video_files = [
	os.path.join(video_dir, f) for f in os.listdir(video_dir)
    if f.endswith(('.mp4', '.avi', '.mov', '.mkv'))
]

# iterate through each video file
for video_file in video_files:
    print(f"Processing video: {video_file}")
    results = model.track(
        source=video_file,
        device=device,
        show=False,
        conf=0.8,
        save=True,
        max_det=5
    )

