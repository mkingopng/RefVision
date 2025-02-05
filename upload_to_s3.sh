#!/usr/bin/env bash
#
# upload_to_s3.sh
#
# Usage:
#   ./upload_to_s3.sh runs/pose/track2/chris_kennedy_squat.mp4 refvision-annotated-videos
#
# This script uploads an MP4 file to an S3 bucket.
# Requires AWS CLI installed and configured with valid credentials.

set -e  # Exit on error
set -x  # Print commands as they run (helpful for debugging, remove if too verbose)

if [ $# -lt 2 ]; then
    echo "Usage: $0 <path-to-local-mp4-file> <s3-bucket-name> [<optional-s3-key>]"
    exit 1
fi

MP4_FILE=$1
S3_BUCKET=$2
S3_KEY=${3:-"$(basename "$MP4_FILE")"}  # Default key is the local filename

if [ ! -f "$MP4_FILE" ]; then
    echo "Error: File '$MP4_FILE' not found."
    exit 1
fi

echo "Uploading '$MP4_FILE' to s3://$S3_BUCKET/$S3_KEY"
aws s3 cp "$MP4_FILE" "s3://$S3_BUCKET/$S3_KEY"
echo "Upload completed successfully."
