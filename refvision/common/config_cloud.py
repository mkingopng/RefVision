# refvision/common/config_cloud.py
"""
cloud configuration
"""
import os
import boto3
from refvision.common.config_base import Config


class CloudConfig(Config):
    """
    cloud configuration
    """

    S3_BUCKET_RAW = os.getenv("S3_BUCKET_RAW", Config.S3_BUCKET_RAW)
    S3_KEY_RAW = os.getenv("VIDEO_KEY", "incoming/raw_video.mp4")
    INGESTION_MODE = os.getenv("INGESTION_MODE", "simulated")
    AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", None)
    AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-southeast-2")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    S3_BUCKET = os.getenv("S3_BUCKET", "refvision-annotated-videos")
    DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "StateStore")
    AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-southeast-2")

    @classmethod
    def get_s3_bucket_raw(cls):
        """
        Returns boto3 client for raw bucket.
        """
        return boto3.client(
            "s3",
            endpoint_url=cls.AWS_ENDPOINT_URL,
            region_name=cls.AWS_DEFAULT_REGION,
            aws_access_key_id=cls.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=cls.AWS_SECRET_ACCESS_KEY,
        )
