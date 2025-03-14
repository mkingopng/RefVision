# refvision/utils/dynamodb_helpers.py
"""
Helper functions for DynamoDB operations.
"""
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key
from refvision.common.config_cloud import CloudConfig


# Initialize the DynamoDB resource using the provided endpoint (for LocalStack) if any.
dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=CloudConfig.AWS_ENDPOINT_URL,
    region_name=CloudConfig.AWS_REGION,
    aws_access_key_id=CloudConfig.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=CloudConfig.AWS_SECRET_ACCESS_KEY,
)

# Get a reference to the table. (It is assumed that the table exists.)
table = dynamodb.Table(CloudConfig.DYNAMODB_TABLE)


def create_item(meet_id, record_id, lifter_name, lift, lift_number, metadata):
    """
    Creates an item in the DynamoDB table.
    :param meet_id: Partition key value.
    :param record_id: Sort key value (e.g., "Alice#Squat#1").
    :param lifter_name: Name of the lifter.
    :param lift: The type of lift (e.g., "Squat").
    :param lift_number: Attempt number.
    :param metadata: Dictionary with additional fields (VideoName, InferenceResult, ExplanationText, etc.).
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


def get_item(meet_id, record_id):
    """
    Retrieves an item from the DynamoDB table.
    :param meet_id: Partition key value.
    :param record_id: Sort key value.
    :return: The item if found, otherwise None.
    """
    response = table.get_item(Key={"MeetID": meet_id, "RecordID": record_id})
    return response.get("Item")


def update_item(meet_id, record_id, updates):
    """
    Updates an item in the DynamoDB table.
    :param record_id:
    :param meet_id:
    :param updates: A dictionary of attribute names and their new values.
    :return: The updated attributes.
    """
    update_expr = "SET "
    expr_attrs = {}
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


def query_items(meet_id):
    """
    Queries the DynamoDB table for all items with the given MeetID.
    :param meet_id:
    :return:
    """
    response = table.query(KeyConditionExpression=Key("MeetID").eq(meet_id))
    return response.get("Items", [])
