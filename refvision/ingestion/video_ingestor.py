# refvision/ingestion/video_ingestor.py
"""
Video ingestion implementations for simulated and live modes.
"""
import os
import boto3
from typing import Protocol
from dotenv import load_dotenv
from refvision.common.config_cloud import CloudConfig


load_dotenv()


class VideoIngestor(Protocol):
    """
    Protocol for video ingestion.
    """

    def ingest(self) -> None:
        """Ingest a video file or stream."""


class SimulatedVideoIngestor:
    """
    Simulated video ingestion
    """

    def __init__(
        self,
        video_path: str,
        bucket: str,
        s3_key: str,
        chunk_size: int = 5 * 1024 * 1024,
    ) -> None:
        self.video_path = video_path
        self.bucket = bucket
        self.s3_key = s3_key
        self.chunk_size = chunk_size
        self.s3_client = CloudConfig.get_s3_bucket_raw()

    def ingest(self) -> None:
        """
        ingest
        :return: None
        """
        try:
            with open(self.video_path, "rb") as f:
                self.s3_client.upload_fileobj(
                    f, self.bucket, self.s3_key, ExtraArgs={"ContentType": "video/mp4"}
                )
            print(f"Uploaded {self.video_path} to s3://{self.bucket}/{self.s3_key}")
        except Exception as e:
            print(f"Error during simulated ingestion: {e}")
            raise e


class LiveVideoIngestor:
    """
    live video ingestor
    """

    def __init__(self, stream_name: str) -> None:
        self.stream_name = stream_name
        self.kinesis_client = boto3.client(
            "kinesisvideo",
            endpoint_url=CloudConfig.AWS_ENDPOINT_URL,
            region_name=CloudConfig.AWS_DEFAULT_REGION,
            aws_access_key_id=CloudConfig.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=CloudConfig.AWS_SECRET_ACCESS_KEY,
        )
        self.s3_client = CloudConfig.get_s3_bucket_raw()

    def ingest(self) -> None:
        """
        Ingest video from a live camera feed to a Kinesis stream.
        :return: None
        """
        self.s3_client.upload_fileobj()
        print(f"Live ingestion to stream {self.stream_name} initiated.")


# Factory function
def get_video_ingestor(video_path: str, bucket: str, s3_key: str) -> VideoIngestor:
    """
    Return the appropriate VideoIngestor based on the current configuration.
    :param video_path:
    :param bucket:
    :param s3_key:
    :return: VideoIngestor
    """
    if CloudConfig.INGESTION_MODE == "live":
        stream_name = os.getenv("STREAM_NAME", "RefVisionVideoStream")
        return LiveVideoIngestor(stream_name)
    else:
        return SimulatedVideoIngestor(video_path, bucket, s3_key)
