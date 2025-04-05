# refvision/utils/dynamodb_helpers.py
"""
Helper functions for DynamoDB operations.
"""
from datetime import datetime
from typing import Any, Dict, Optional
import boto3
from boto3.dynamodb.conditions import Key
from refvision.common.config import get_config
from dotenv import load_dotenv

load_dotenv()
cfg = get_config()

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=cfg["AWS_ENDPOINT_URL"],
    region_name=cfg["AWS_REGION"],
    aws_access_key_id=cfg["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=cfg["AWS_SECRET_ACCESS_KEY"],
)

table = dynamodb.Table(cfg["DYNAMODB_TABLE"])


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
    Updates an item in the DynamoDB table, including attributes such as "Status"
    which is a reserved word. We fix this by using expression attribute names.
    :param meet_id: Partition key value.
    :param record_id: Sort key value.
    :param updates: A dictionary of attribute names and their new values.
    :return: The updated attributes if successful, otherwise None.
    """

    # build placeholders for each attribute
    update_expr_parts = []
    expr_attr_names: Dict[str, str] = {}
    expr_attr_values: Dict[str, Any] = {}

    i = 0
    for key, value in updates.items():
        # for each attribute, define a placeholder for the name and one for the value
        name_placeholder = f"#attr{i}"  # e.g. #attr0, #attr1, etc.
        value_placeholder = f":val{i}"

        # if the key is "Status" (which is reserved), map it to something like "#st"
        if key.lower() == "status":
            name_placeholder = "#st"
            expr_attr_names["#st"] = "Status"
        else:
            # otherwise just use the generic placeholder
            expr_attr_names[name_placeholder] = key

        expr_attr_values[value_placeholder] = value
        update_expr_parts.append(f"{name_placeholder} = {value_placeholder}")
        i += 1

    # build the final UpdateExpression, e.g. "SET #attr0 = :val0, #attr1 = :val1"
    update_expr = "SET " + ", ".join(update_expr_parts)

    response = table.update_item(
        Key={"MeetID": meet_id, "RecordID": record_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values,
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
