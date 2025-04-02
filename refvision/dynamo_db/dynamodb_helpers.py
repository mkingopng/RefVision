# refvision/utils/dynamodb_helpers.py
"""
Helper functions for DynamoDB operations.
"""

import os
from datetime import datetime
from typing import Any, Dict, Optional
import boto3
from boto3.dynamodb.conditions import Key
from refvision.common.config_cloud import CloudConfig

# local endpoint for local dev (optional):
LOCAL_DYNAMODB_ENDPOINT = os.getenv("http://localhost:8000")

# switch between local vs AWS:
if LOCAL_DYNAMODB_ENDPOINT:
    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url=LOCAL_DYNAMODB_ENDPOINT,
        region_name=CloudConfig.AWS_REGION,
        aws_access_key_id="fakeKey",
        aws_secret_access_key="fakeSecret",
    )
else:
    # production  usage
    dynamodb = boto3.resource(
        "dynamodb",
        endpoint_url=CloudConfig.AWS_ENDPOINT_URL,
        region_name=CloudConfig.AWS_REGION,
        aws_access_key_id=CloudConfig.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=CloudConfig.AWS_SECRET_ACCESS_KEY,
    )

table = dynamodb.Table(CloudConfig.DYNAMODB_TABLE)


def create_item(
    meet_id: str,
    record_id: str,
    lifter_name: str,
    lift: str,
    lift_number: int,
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Creates an item in the DynamoDB table.
    :param meet_id: Partition key value.
    :param record_id: Sort key value (e.g. "Alice#Squat#1").
    :param lifter_name: Name of the lifter.
    :param lift: Type of lift (e.g. "Squat").
    :param lift_number: Attempt number.
    :param metadata: Dictionary with additional fields (VideoName, InferenceResult, etc.).
    :return: The item that was written.
    """
    now = datetime.utcnow().isoformat()
    item = {
        "MeetID": meet_id,
        "RecordID": record_id,
        "LifterName": lifter_name,
        "Lift": lift,
        "LiftNumber": str(lift_number),
        "CreatedAt": now,
        "VideoName": metadata.get("VideoName", ""),
        "InferenceResult": metadata.get("InferenceResult", ""),
        "ExplanationText": metadata.get("ExplanationText", ""),
        "ErrorMessage": metadata.get("ErrorMessage", ""),
        "Status": metadata.get("Status", "PENDING"),
    }
    table.put_item(Item=item)
    return item


def get_item(meet_id: str, record_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves an item from the DynamoDB table.
    :param meet_id: Partition key value.
    :param record_id: Sort key value.
    :return: The item if found, otherwise None.
    """
    response = table.get_item(Key={"MeetID": meet_id, "RecordID": record_id})
    return response.get("Item")


def update_item(
    meet_id: str, record_id: str, updates: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Updates an item in the DynamoDB table.
    :param meet_id: Partition key value.
    :param record_id: Sort key value.
    :param updates: A dictionary of attribute names and their new values.
    :return: The updated attributes if successful, otherwise None.
    """
    update_expr = "SET "
    expr_attrs: Dict[str, Any] = {}
    for i, (key, value) in enumerate(updates.items()):
        placeholder = f":val{i}"
        update_expr += f"{key} = {placeholder}, "
        expr_attrs[placeholder] = value
    update_expr = update_expr.rstrip(", ")

    response = table.update_item(
        Key={"MeetID": meet_id, "RecordID": record_id},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_attrs,
        ReturnValues="ALL_NEW",
    )
    return response.get("Attributes")


def query_items(meet_id: str) -> Any:
    """
    Queries the DynamoDB table for all items with the given meet_id (partition key).
    :param meet_id: Partition key value.
    :return: A list of items if found, otherwise an empty list.
    """
    response = table.query(KeyConditionExpression=Key("MeetID").eq(meet_id))
    return response.get("Items", [])
