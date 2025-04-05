# refvision/ingestion/s3_client.py
"""
get S3 client
"""
import boto3


def get_s3_client():
    """Returns a real AWS S3 client without LocalStack"""
    return boto3.client("s3")
