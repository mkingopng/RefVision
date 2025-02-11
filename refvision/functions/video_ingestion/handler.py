# functions/video_ingestion/handler.py
"""
This module is responsible for handling the ingestion of videos.
"""
import boto3
import json
import os

s3_client = boto3.client("s3", region_name=os.getenv("AWS_DEFAULT_REGION"))
kinesis_client = boto3.client("kinesis", region_name=os.getenv("AWS_DEFAULT_REGION"))

def lambda_handler(event, context):
    """Processes incoming video streams from Kinesis and saves them to S3."""
    for record in event["Records"]:
        payload = json.loads(record["body"])
        video_key = payload["video_key"]

        # Upload to S3
        s3_client.put_object(
            Bucket=os.getenv("S3_BUCKET"),
            Key=f"uploads/{video_key}",
            Body=payload["video_data"]
        )

        # Acknowledge processing
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Video processed and stored"})
        }