# tests/test_video_ingestor.py
"""
Test the video ingestor module.
usage: poetry run pytest tests/test_video_ingestor.py
"""
import os
import boto3
import pytest
import time
from refvision.ingestion.video_ingestor import get_video_ingestor

# Use the TEST_S3_BUCKET from .env (which we now set to us-east-1)
TEST_BUCKET = os.getenv("TEST_S3_BUCKET", "local-test-bucket")
TEST_KEY = "Keeta_squat_1.mp4"
# Adjust the path if necessary
TEST_VIDEO_PATH = os.path.join(os.getcwd(), "data", "raw_data", "Keeta_squat_1.mp4")

# Initialize the S3 client using the environment variables.
s3 = boto3.client(
    's3',
    endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

@pytest.fixture(scope="module")
def create_test_bucket():
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    try:
        if region != "us-east-1":
            s3.create_bucket(
                Bucket=TEST_BUCKET,
                CreateBucketConfiguration={"LocationConstraint": region}
            )
        else:
            s3.create_bucket(Bucket=TEST_BUCKET)
        print(f"Created test bucket: {TEST_BUCKET}")
    except Exception as e:
        print(f"Bucket {TEST_BUCKET} might already exist: {e}")
    time.sleep(1)  # Give LocalStack a moment to register the new bucket.
    yield
    # Clean up: delete all objects and then the bucket.
    try:
        response = s3.list_objects_v2(Bucket=TEST_BUCKET)
        for obj in response.get("Contents", []):
            s3.delete_object(Bucket=TEST_BUCKET, Key=obj["Key"])
    except Exception as e:
        print(f"Error cleaning up bucket contents: {e}")
    try:
        s3.delete_bucket(Bucket=TEST_BUCKET)
        print(f"Deleted test bucket: {TEST_BUCKET}")
    except Exception as e:
        print(f"Error deleting bucket {TEST_BUCKET}: {e}")

def test_simulated_video_ingestion(create_test_bucket):
    ingestor = get_video_ingestor(TEST_VIDEO_PATH, TEST_BUCKET, TEST_KEY)
    ingestor.ingest()
    time.sleep(1)  # Allow some time for the upload to complete.
    response = s3.list_objects_v2(Bucket=TEST_BUCKET, Prefix=TEST_KEY)
    objects = response.get("Contents", [])
    assert len(objects) > 0, "No objects found in the bucket after ingestion"
