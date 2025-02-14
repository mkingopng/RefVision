# tests/test_dynamodb_helpers.py
"""
Unit tests for DynamoDB helper functions.
Run these tests with:
    poetry run pytest tests/test_dynamodb_helpers.py
"""

import os
import boto3
import pytest
from refvision.utils import dynamodb_helpers

# Create a boto3 DynamoDB resource for test setup using the environment variables.
dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
    region_name=os.getenv("AWS_DEFAULT_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

TABLE_NAME = os.getenv("DYNAMODB_TABLE")


@pytest.fixture(scope="session", autouse=True)
def create_test_table():
    # Create a test table in LocalStack.
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "MeetID", "KeyType": "HASH"},
                {"AttributeName": "RecordID", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "MeetID", "AttributeType": "S"},
                {"AttributeName": "RecordID", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )
        table.meta.client.get_waiter("table_exists").wait(TableName=TABLE_NAME)
    except Exception as e:
        # If the table already exists, that's fine.
        print(f"Table {TABLE_NAME} might already exist: {e}")
    yield
    # Clean up: delete the table after tests.
    table = dynamodb.Table(TABLE_NAME)
    table.delete()
    table.meta.client.get_waiter("table_not_exists").wait(TableName=TABLE_NAME)


def test_create_and_get_item():
    meet_id = "TestMeet"
    record_id = "Alice#Squat#1"  # Composite key (RecordID)
    lifter_name = "Alice"
    lift = "Squat"
    lift_number = 1
    metadata = {
        "VideoName": "test_video.mp4",
        "InferenceResult": "Good Lift!",
        "ExplanationText": "Hips were below knees.",
    }
    # Create an item using the create_item function.
    item = dynamodb_helpers.create_item(
        meet_id, record_id, lifter_name, lift, lift_number, metadata
    )
    assert item["MeetID"] == meet_id
    assert item["RecordID"] == record_id
    assert item["LifterName"] == lifter_name
    assert item["Lift"] == lift
    assert item["LiftNumber"] == str(lift_number)
    # Retrieve the same item.
    retrieved_item = dynamodb_helpers.get_item(meet_id, record_id)
    assert retrieved_item == item


def test_update_item():
    meet_id = "TestMeet"
    record_id = "Alice#Squat#2"
    lifter_name = "Alice"
    lift = "Squat"
    lift_number = 2
    metadata = {
        "VideoName": "test_video2.mp4",
        "InferenceResult": "No Lift",
        "ExplanationText": "",
    }
    # Create an item.
    dynamodb_helpers.create_item(
        meet_id, record_id, lifter_name, lift, lift_number, metadata
    )
    # Update the item by changing InferenceResult and ExplanationText.
    updates = {
        "InferenceResult": "Good Lift!",
        "ExplanationText": "Hips were lower than knees.",
    }
    updated = dynamodb_helpers.update_item(meet_id, record_id, updates)
    assert updated["InferenceResult"] == "Good Lift!"
    assert updated["ExplanationText"] == "Hips were lower than knees."


def test_query_items():
    meet_id = "TestMeetQuery"
    lifter_name = "Alice"
    lift = "Squat"
    # Create multiple items.
    for i in range(3):
        record_id = f"Alice#Squat#{i}"
        metadata = {
            "VideoName": f"video_{i}.mp4",
            "InferenceResult": "Good Lift!",
            "ExplanationText": "",
        }
        dynamodb_helpers.create_item(meet_id, record_id, lifter_name, lift, i, metadata)
    # Query items for this meet.
    items = dynamodb_helpers.query_items(meet_id)
    matching_items = [item for item in items if item["MeetID"] == meet_id]
    assert len(matching_items) >= 3
