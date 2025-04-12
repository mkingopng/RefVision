# refvision/ingestion/handler.py
"""
Lambda handler module responsible for handling video ingestion events.
Triggers simulated or live ingestion based on configuration.
"""
import json
from typing import Any, Dict
from refvision.ingestion.video_ingestor import (
    LiveVideoIngestor,
    SimulatedVideoIngestor,
    VideoIngestor,
)
from refvision.common.config import config_data


def lambda_handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    AWS Lambda handler function to trigger video ingestion.
    :param event: AWS Lambda event payload, expected to contain S3 event information.
    :return: Response indicating the result of ingestion operation.
    """
    video_key = event["Records"][0]["s3"]["object"]["key"]

    ingestor: VideoIngestor

    if config_data.INGESTION_MODE.lower() == "live":
        ingestor = LiveVideoIngestor(stream_name=config_data.VIDEO_STREAM_NAME)
    else:
        video_path = f"/tmp/{video_key}"
        ingestor = SimulatedVideoIngestor(
            video_path=video_path,
            bucket=config_data.S3_BUCKET_RAW,
            s3_key=video_key,
        )

    ingestor.ingest()

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Video ingestion triggered."}),
    }
