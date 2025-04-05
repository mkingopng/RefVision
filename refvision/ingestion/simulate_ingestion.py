# refvision/ingestion/simulate_ingestion.py
"""
Simulate local ingestion of a .mov video into S3 using the SimulatedVideoIngestor.
"""

import os
import argparse
from refvision.common.config import get_config
from refvision.ingestion.video_ingestor import get_video_ingestor


def main():
    """
    simulate ingestion
    :return:
    """
    parser = argparse.ArgumentParser(
        description="Simulate ingestion of a local .mov file into S3"
    )
    parser.add_argument(
        "--local-video", required=True, help="Path to the local .mov/.mp4 video"
    )
    parser.add_argument(
        "--s3-key",
        default="incoming/local_squat.mov",
        help="S3 key name to store the video under",
    )
    args = parser.parse_args()

    # 1) load config dictionary
    cfg = get_config()
    # for example, let's assume the S3 bucket name is in cfg["RAW_BUCKET"] or cfg["S3_BUCKET_RAW"].
    s3_bucket = cfg["RAW_BUCKET"]  # or "refvision-raw-videos", etc.

    local_path = os.path.abspath(args.local_video)
    s3_key = args.s3_key

    # 2) instantiate the correct ingestor (which will be SimulatedVideoIngestor if INGESTION_MODE != "live")
    ingestor = get_video_ingestor(local_path, s3_bucket, s3_key)

    # 3) call ingest() to upload the local file to S3
    print(f"Simulating ingestion from local path: {local_path}")
    ingestor.ingest()
    print(f"Done! Video is now at s3://{s3_bucket}/{s3_key}")


if __name__ == "__main__":
    main()
