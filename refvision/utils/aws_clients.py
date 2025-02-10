# refvision/utils/aws_clients.py
"""

"""
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

# Initialize the S3 client using environment variables.
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION"),
    endpoint_url=os.getenv("AWS_ENDPOINT_URL")
)

# You can also add other AWS clients here as needed, e.g., for Kinesis or DynamoDB.
