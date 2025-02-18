#
"""

"""
import base64
import gzip
import json
import os
import time
from typing import Any, Dict, List, Optional

import boto3

# Get the combined log group name from the environment variable.
COMBINED_LOG_GROUP: str = os.environ.get(
    "COMBINED_LOG_GROUP", "/aws/refvision/combined"
)
logs_client = boto3.client("logs")


def create_log_stream(log_group: str, log_stream: str) -> None:
    """
    Create a new log stream in the specified log group.
    :param log_group: (str) The name of the CloudWatch log group.
    :param log_stream: (str) The name of the log stream to create.
    :Raises: Any exception thrown by the AWS SDK if the creation fails,
    except for ResourceAlreadyExistsException which is caught.
    :returns: None
    """
    try:
        logs_client.create_log_stream(logGroupName=log_group, logStreamName=log_stream)
    except logs_client.exceptions.ResourceAlreadyExistsException:
        # If the log stream already exists, do nothing.
        pass


def get_sequence_token(log_group: str, log_stream: str) -> Optional[str]:
    """
    Retrieve the upload sequence token for a given log stream.
    :param log_group: (str) The name of the CloudWatch log group.
    :param log_stream: (str) The name of the log stream.
    :returns: Optional[str] The current upload sequence token if available,
    otherwise None.
    """
    response: Dict[str, Any] = logs_client.describe_log_streams(
        logGroupName=log_group, logStreamNamePrefix=log_stream
    )
    streams: List[Dict[str, Any]] = response.get("logStreams", [])
    if streams and "uploadSequenceToken" in streams[0]:
        return streams[0]["uploadSequenceToken"]
    return None


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for processing CloudWatch Logs subscription events and
    forwarding them to a combined log group. The incoming event is expected to
    be in the format delivered by CloudWatch Logs,which is base64-encoded and
    gzipped.
    :param event: (Dict[str, Any]) The event payload from CloudWatch Logs.
    :param context: (Any) Lambda context object (unused in this implementation)
    :returns: Dict[str, Any]: A dictionary with the HTTP status code and a
    message.
    """
    # Decode and decompress the CloudWatch Logs event.
    compressed_data: bytes = base64.b64decode(event["awslogs"]["data"])
    decompressed_data: bytes = gzip.decompress(compressed_data)
    payload: Dict[str, Any] = json.loads(decompressed_data)

    # Create a unique log stream name using the current timestamp.
    log_stream_name: str = "forwarded-" + str(int(time.time()))
    create_log_stream(COMBINED_LOG_GROUP, log_stream_name)

    log_events_raw: List[Dict[str, Any]] = payload.get("logEvents", [])
    if not log_events_raw:
        return {"statusCode": 200, "body": "No log events to process."}

    # Prepare log events in the required format.
    log_events: List[Dict[str, Any]] = []
    for log_event in log_events_raw:
        log_events.append(
            {"timestamp": log_event["timestamp"], "message": log_event["message"]}
        )

    # Retrieve the next sequence token for the log stream.
    sequence_token: Optional[str] = get_sequence_token(
        COMBINED_LOG_GROUP, log_stream_name
    )

    put_events_kwargs: Dict[str, Any] = {
        "logGroupName": COMBINED_LOG_GROUP,
        "logStreamName": log_stream_name,
        "logEvents": log_events,
    }
    if sequence_token:
        put_events_kwargs["sequenceToken"] = sequence_token

    # write the log events to the combined log group.
    logs_client.put_log_events(**put_events_kwargs)

    return {"statusCode": 200, "body": "Log events forwarded successfully."}
