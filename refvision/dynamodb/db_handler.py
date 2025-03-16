# refvision/dynamodb/db_handler.py
"""

"""
import boto3
import os
from botocore.exceptions import ClientError

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
USE_LOCAL_DYNAMODB = os.getenv("USE_LOCAL_DYNAMODB", "False").lower() == "true"

if USE_LOCAL_DYNAMODB:
    dynamodb = boto3.resource("dynamodb", endpoint_url="http://localhost:8000")
else:
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

table = dynamodb.Table("PowerliftingMeet")


def store_data(meet_id: str, lifter: str, attempt_number: int, data: dict):
    """
    Store or update data in DynamoDB.
    :param meet_id: ID of the meet.
    :param lifter: Lifter's name or ID.
    :param attempt_number: Attempt number.
    :param data: Dictionary of data to store.
    """
    try:
        table.update_item(
            Key={
                "meet_id": meet_id,
                "lifter": lifter,
                "attempt_number": attempt_number,
            },
            UpdateExpression="SET info = :data",
            ExpressionAttributeValues={":data": data},
        )
    except ClientError as e:
        raise RuntimeError(f"DynamoDB storage error: {e}")


def get_data(meet_id: str, lifter: str, attempt_number: int) -> dict:
    """
    Retrieve stored data from DynamoDB.
    """
    try:
        response = table.get_item(
            Key={"meet_id": meet_id, "lifter": lifter, "attempt_number": attempt_number}
        )
        item = response.get("Item")
        if not item:
            return {}
        return item.get("info", {})
    except ClientError as e:
        raise RuntimeError(f"DynamoDB retrieval error: {e}")
