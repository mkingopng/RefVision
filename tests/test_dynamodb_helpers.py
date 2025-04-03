# tests/test_dynamodb_helpers.py
"""
Unit tests for DynamoDB helper functions.
Run these tests with:
    poetry run pytest tests/test_dynamodb_helpers.py
"""

# import os
# import boto3
# import botocore.exceptions
# import pytest
# from refvision.dynamo_db import dynamodb_helpers
# from refvision.common.config_local import LocalConfig as Config
#
# pytestmark = pytest.mark.skipif(
#     Config.FLASK_APP_MODE.lower() == "local",
#     reason="Skipping AWS infra tests in local mode",
# )
#
# TABLE_NAME = os.getenv("DYNAMODB_TABLE", "RefVisionMeetVirtualRefereeDecisions")
#
# dynamodb = boto3.resource(
#     "dynamodb", region_name=os.getenv("AWS_DEFAULT_REGION", "ap-southeast-2")
# )
#
#
# @pytest.fixture(scope="session", autouse=True)
# def create_test_table():
#     """
#     Create a test table before running tests and delete it after.
#     :return:
#     """
#     try:
#         table = dynamodb.create_table(
#             TableName=TABLE_NAME,
#             KeySchema=[
#                 {"AttributeName": "MeetID", "KeyType": "HASH"},
#                 {"AttributeName": "RecordID", "KeyType": "RANGE"},
#             ],
#             AttributeDefinitions=[
#                 {"AttributeName": "MeetID", "AttributeType": "S"},
#                 {"AttributeName": "RecordID", "AttributeType": "S"},
#             ],
#             ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
#         )
#         table.meta.client.get_waiter("table_exists").wait(TableName=TABLE_NAME)
#     except botocore.exceptions.ClientError as e:
#         error_code = e.response["Error"]["Code"]
#         if error_code == "ResourceInUseException":
#             print(f"Table {TABLE_NAME} already exists.")
#             table = dynamodb.Table(TABLE_NAME)
#         else:
#             pytest.skip(f"Cannot create DynamoDB table {TABLE_NAME}: {e}")
#     yield
#     # Teardown: delete the table after tests.
#     try:
#         table.delete()
#     except Exception as e:
#         print(f"Error deleting table {TABLE_NAME}: {e}")
#
#
# def test_create_and_get_item():
#     meet_id = "TestMeet"
#     record_id = "Alice#Squat#1"  # Composite key (RecordID)
#     lifter_name = "Alice"
#     lift = "Squat"
#     lift_number = 1
#     metadata = {
#         "VideoName": "test_video.mp4",
#         "InferenceResult": "Good Lift!",
#         "ExplanationText": "Hips were below knees.",
#     }
#     # Create an item using the create_item function.
#     item = dynamodb_helpers.create_item(
#         meet_id, record_id, lifter_name, lift, lift_number, metadata
#     )
#     assert item["MeetID"] == meet_id
#     assert item["RecordID"] == record_id
#     assert item["LifterName"] == lifter_name
#     assert item["Lift"] == lift
#     assert item["LiftNumber"] == str(lift_number)
#     # Retrieve the same item.
#     retrieved_item = dynamodb_helpers.get_item(meet_id, record_id)
#     assert retrieved_item == item
#
#
# def test_update_item():
#     meet_id = "TestMeet"
#     record_id = "Alice#Squat#2"
#     lifter_name = "Alice"
#     lift = "Squat"
#     lift_number = 2
#     metadata = {
#         "VideoName": "test_video2.mp4",
#         "InferenceResult": "No Lift",
#         "ExplanationText": "",
#     }
#     # Create an item.
#     dynamodb_helpers.create_item(
#         meet_id, record_id, lifter_name, lift, lift_number, metadata
#     )
#     # Update the item by changing InferenceResult and ExplanationText.
#     updates = {
#         "InferenceResult": "Good Lift!",
#         "ExplanationText": "Hips were lower than knees.",
#     }
#     updated = dynamodb_helpers.update_item(meet_id, record_id, updates)
#     assert updated["InferenceResult"] == "Good Lift!"
#     assert updated["ExplanationText"] == "Hips were lower than knees."
#
#
# def test_query_items():
#     meet_id = "TestMeetQuery"
#     lifter_name = "Alice"
#     lift = "Squat"
#     # Create multiple items.
#     for i in range(3):
#         record_id = f"Alice#Squat#{i}"
#         metadata = {
#             "VideoName": f"video_{i}.mp4",
#             "InferenceResult": "Good Lift!",
#             "ExplanationText": "",
#         }
#         dynamodb_helpers.create_item(meet_id, record_id, lifter_name, lift, i, metadata)
#
#     # Query items for this meet.
#     items = dynamodb_helpers.query_items(meet_id)
#     matching_items = [item for item in items if item["MeetID"] == meet_id]
#     assert len(matching_items) >= 3
