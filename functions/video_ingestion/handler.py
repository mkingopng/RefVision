# functions/video_ingestion/handler.py
"""
This module is responsible for handling the ingestion of videos.
"""
import boto3
import json
import os
import time
from typing import Any, Dict

# Initialize AWS clients
kinesis_client = boto3.client('kinesis')
firehose_client = boto3.client('firehose')

# Environment variables
STREAM_NAME = os.environ.get('STREAM_NAME')
DELIVERY_STREAM_NAME = os.environ.get('DELIVERY_STREAM_NAME')

if not STREAM_NAME or not DELIVERY_STREAM_NAME:
    raise ValueError("Missing required environment variables: STREAM_NAME or DELIVERY_STREAM_NAME")

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handles video ingestion requests by simulating streaming data to Kinesis
    and Firehose.
    :param event: (Dict[str, Any]) The event data passed to the Lambda function.
    :param context: (Any) The runtime information of the Lambda function.
    :return: Dict[str, Any]: A response indicating the status of the ingestion
    process.
    """
    try:
        # Extract video metadata from the event
        video_id = event.get('video_id', 'test_video.mp4')
        chunk_id = event.get('chunk_id', '0001')
        payload = {
            "video_id": video_id,
            "chunk_id": chunk_id,
            "data": "Sample video chunk data"
        }

        # Stream data to Kinesis
        kinesis_response = kinesis_client.put_record(
            StreamName=STREAM_NAME,
            Data=json.dumps(payload),
            PartitionKey=video_id
        )

        # Send data to Firehose
        firehose_response = firehose_client.put_record(
            DeliveryStreamName=DELIVERY_STREAM_NAME,
            Record={
                'Data': json.dumps(payload) + '\n'
            }
        )

        # Return success response
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Video ingestion successful!",
                "kinesis_response": kinesis_response,
                "firehose_response": firehose_response
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Video ingestion failed!",
                "error": str(e)
            })
        }

def mock_video_stream(file_path: str, chunk_size: int = 1024, delay: float = 0.5) -> None:
    """
    Simulates streaming a video file to Kinesis and Firehose by reading chunks of data.
    :param file_path: (str) Path to the video file.
    :param chunk_size: (int) Size of each data chunk in bytes.
    :param delay: (float) Delay between sending each chunk (in seconds).
    """
    video_id = os.path.basename(file_path)
    try:
        with open(file_path, 'rb') as video_file:
            chunk_id = 0
            while chunk := video_file.read(chunk_size):
                payload = {
                    "video_id": video_id,
                    "chunk_id": str(chunk_id),
                    "data": chunk.hex()
                }

                # Send chunk to Kinesis
                kinesis_client.put_record(
                    StreamName=STREAM_NAME,
                    Data=json.dumps(payload),
                    PartitionKey=video_id
                )

                # Send chunk to Firehose
                firehose_client.put_record(
                    DeliveryStreamName=DELIVERY_STREAM_NAME,
                    Record={
                        'Data': json.dumps(payload) + '\n'
                    }
                )

                print(f"Sent chunk {chunk_id}")
                chunk_id += 1
                time.sleep(delay)

    except Exception as e:
        print(f"Error during streaming: {str(e)}")
