# refvision/ingestion/video_ingestor.py
"""
ingest video files into the pipeline
"""
import os
import boto3
from dotenv import load_dotenv
from time import sleep

load_dotenv()

INGESTION_MODE = os.getenv("INGESTION_MODE", "simulated")
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", None)
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-southeast-2")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET = os.getenv("S3_BUCKET", "refvision-annotated-videos")  # For production, set accordingly

# Initialize an S3 client (or Firehose client if needed) using boto3
s3_client = boto3.client(
    's3',
    endpoint_url=AWS_ENDPOINT_URL,
    region_name=AWS_DEFAULT_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

class SimulatedVideoIngestor:
    """
    A simulated video ingestor that reads a pre-recorded video file and uploads it
    to S3 (or sends chunks via Firehose) to simulate live ingestion.
    """
    def __init__(
			self,
			video_path: str,
			bucket: str,
			s3_key: str,
			chunk_size: int = 5 * 1024 * 1024):
        """
        :param video_path: Path to the local pre-recorded video file.
        :param bucket: The S3 bucket to upload the video/chunks.
        :param s3_key: The key (path) in S3 where the video will be stored.
        :param chunk_size: Size in bytes for each chunk (optional).
        """
        self.video_path = video_path
        self.bucket = bucket
        self.s3_key = s3_key
        self.chunk_size = chunk_size

    def ingest(self):
        """
        Ingest the video file by uploading it to S3.
        In a more advanced implementation, you could split the video into
        chunks and upload them sequentially, with delays between uploads to
        simulate streaming.
        """
        print(f"Simulated ingestion: Uploading {self.video_path} to s3://{self.bucket}/{self.s3_key}")
        try:
            with open(self.video_path, 'rb') as f:
                # For simplicity, we upload the entire file.
                s3_client.upload_fileobj(
                    f,
                    self.bucket,
                    self.s3_key,
                    ExtraArgs={"ContentType": "video/mp4"}
                )
            print("Upload successful.")
        except Exception as e:
            print(f"Error during simulated ingestion: {e}")
            raise e


class LiveVideoIngestor:
    """
    (Production version) A video ingestor that uses Kinesis Video Streams or Firehose
    to ingest live video.
    """
    def __init__(self, stream_name: str):
        self.stream_name = stream_name
        # Initialize your Kinesis Video Streams client or Firehose client as needed.
        self.kinesis_client = boto3.client(
            'kinesisvideo',
            endpoint_url=AWS_ENDPOINT_URL,
            region_name=AWS_DEFAULT_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        # Add additional setup here

    def ingest(self):
        """
        Ingest live video. This is a stub implementation.
        """
        print(f"Live ingestion for stream {self.stream_name} is not yet implemented.")
        # Here you would integrate with your live camera feed and push data to the stream.


def get_video_ingestor(
		video_path: str,
		s3_bucket: str,
		s3_key: str
):
    """
    Factory function to return the appropriate Video Ingestor based on configuration.
    :param video_path: Path to the local pre-recorded video file.
    :param s3_bucket: The S3 bucket to upload the video/chunks.
    :param s3_key: The key (path) in S3 where the video will be stored.
    """
    if INGESTION_MODE.lower() == "live":
        # For production, return the live ingestor.
        # You might also need additional configuration for live ingestion.
        stream_name = os.getenv("STREAM_NAME", "RefVisionVideoStream")
        return LiveVideoIngestor(stream_name)
    else:
        # Default to simulated ingestion for local testing.
        return SimulatedVideoIngestor(video_path, s3_bucket, s3_key)
