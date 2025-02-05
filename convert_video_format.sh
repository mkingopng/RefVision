# convert_video_format.sh
poetry run python src/main.py --video "$VIDEO_FILE" --model_path "$MODEL_PATH"
AVI_FILE="runs/pose/track2/chris_kennedy_squat.avi"
MP4_FILE="runs/pose/track2/chris_kennedy_squat.mp4"

if [ -f "$AVI_FILE" ]; then
    ffmpeg -y -i "$AVI_FILE" -c:v libx264 -pix_fmt yuv420p "$MP4_FILE"
    rm "$AVI_FILE"
fi
