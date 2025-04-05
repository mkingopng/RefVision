# refvision/ingestion/video_ingestor.py
"""
Video ingestion module for RefVision.
"""
import boto3
from typing import Protocol
from refvision.common.config import get_config

cfg = get_config()


class VideoIngestor(Protocol):
    """Protocol for video ingestion."""

    def ingest(self) -> None:
        """Ingest a video file or stream."""


class SimulatedVideoIngestor:
    """Simulated video ingestion for testing purposes."""

    def __init__(self, video_path: str, bucket: str, s3_key: str) -> None:
        """
        Initialize the simulated video ingestor.
        :param video_path:
        :param bucket:
        :param s3_key:
        """
        self.video_path = video_path
        self.bucket = bucket
        self.s3_key = s3_key
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=cfg["AWS_ENDPOINT_URL"],
            region_name=cfg["AWS_DEFAULT_REGION"],
            aws_access_key_id=cfg["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=cfg["AWS_SECRET_ACCESS_KEY"],
        )

    def ingest(self) -> None:
        try:
            with open(self.video_path, "rb") as f:
                self.s3_client.upload_fileobj(
                    f,
                    self.bucket,
                    self.s3_key,
                    ExtraArgs={"ContentType": "video/mp4"},
                )
            print(f"Uploaded {self.video_path} to s3://{self.bucket}/{self.s3_key}")
        except Exception as e:
            print(f"Error during simulated ingestion: {e}")
            raise


class LiveVideoIngestor:
    """Live video ingestion from a camera feed."""

    def __init__(self, stream_name: str) -> None:
        """
        Initialize the live video ingestor.
        :param stream_name:
        :return None:
        """
        self.stream_name = stream_name
        # possibly talk to Kinesis Video or do something else
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=cfg["AWS_ENDPOINT_URL"],
            region_name=cfg["AWS_DEFAULT_REGION"],
            aws_access_key_id=cfg["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=cfg["AWS_SECRET_ACCESS_KEY"],
        )

    def ingest(self) -> None:
        # TODO: Actually read from a live camera feed, or from Kinesis Video Streams
        # Currently incomplete:
        # This call is incomplete—there's no local file or streaming data passed to upload_fileobj()
        print("Live ingestion not yet implemented")


def get_video_ingestor(video_path: str, bucket: str, s3_key: str) -> VideoIngestor:
    """
    Factory function to get the appropriate video ingestor based on the ingestion mode.
    :param video_path:
    :param bucket:
    :param s3_key:
    :return: VideoIngestor
    """
    if cfg["INGESTION_MODE"] == "live":
        stream_name = cfg["VIDEO_STREAM_NAME"]
        return LiveVideoIngestor(stream_name)
    else:
        return SimulatedVideoIngestor(video_path, bucket, s3_key)
