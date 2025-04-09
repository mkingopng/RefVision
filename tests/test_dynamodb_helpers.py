# tests/test_dynamodb_helpers.py
"""
Unit tests for DynamoDB helper functions.
"""
import os
import boto3
import botocore.exceptions
import pytest

from refvision.dynamo_db import dynamodb_helpers

TABLE_NAME = os.getenv("DYNAMODB_TABLE", "RefVisionMeetVirtualRefereeDecisions")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "ap-southeast-2")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)


@pytest.fixture(scope="session", autouse=True)
def create_test_table():
    """
    Creates (or re-uses) a DynamoDB table for these tests, and deletes it after.
    You need AWS credentials that allow table creation and deletion.
    """
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
        print(f"Created DynamoDB table '{TABLE_NAME}'.")
    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "ResourceInUseException":
            print(f"Table '{TABLE_NAME}' already exists. Re-using it for tests.")
        else:
            pytest.skip(f"Cannot create DynamoDB table {TABLE_NAME}: {e}")

    yield


def test_create_and_get_item():
    meet_id = "TestMeet"
    record_id = "Alice#Squat#1"
    lifter_name = "Alice"
    lift = "Squat"
    lift_number = 1
    metadata = {
        "VideoName": "test_video.mp4",
        "InferenceResult": "Good Lift!",
        "ExplanationText": "Hips were below knees.",
    }

    item = dynamodb_helpers.create_item(
        meet_id, record_id, lifter_name, lift, lift_number, metadata
    )
    assert item["MeetID"] == meet_id
    assert item["RecordID"] == record_id
    assert item["LifterName"] == lifter_name
    assert item["Lift"] == lift
    assert item["LiftNumber"] == str(lift_number)

    retrieved_item = dynamodb_helpers.get_item(meet_id, record_id)
    assert retrieved_item is not None
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

    dynamodb_helpers.create_item(
        meet_id, record_id, lifter_name, lift, lift_number, metadata
    )

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

    for i in range(3):
        record_id = f"{lifter_name}#{lift}#{i}"
        metadata = {
            "VideoName": f"video_{i}.mp4",
            "InferenceResult": "Good Lift!",
        }
        dynamodb_helpers.create_item(meet_id, record_id, lifter_name, lift, i, metadata)

    items = dynamodb_helpers.query_items(meet_id)
    matching_items = [it for it in items if it["MeetID"] == meet_id]
    assert len(matching_items) >= 3
