#!/usr/bin/env bash
# run_inference.sh
# Example usage: ./run_inference.sh data/raw_data/chris_kennedy_squat.mp4

set -e
set -x

VIDEO_FILE=$1

if [ -z "$VIDEO_FILE" ]; then
  echo "Usage: ./run_inference.sh data/raw_data/chris_kennedy_squat.mp4"
  exit 1
fi

# check file exists:
if [ ! -f "$VIDEO_FILE" ]; then
  echo "Error: Video file '$VIDEO_FILE' not found."
  exit 1
fi

# the model
MODEL_PATH="./model_zoo/yolo11x-pose.pt"

# Run the Python script with Poetry
poetry run python src/main.py \
  --video "$VIDEO_FILE" \
  --model_path "$MODEL_PATH"

# After completion, the annotated video is saved to runs/pose/track/.
# The terminal should print "Video: ... => Decision: PASS/FAIL"