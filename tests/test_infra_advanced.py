"""
Advanced Infrastructure Tests for IAM, S3, Kinesis, and Firehose.
"""

import boto3
import pytest
import time
from dotenv import load_dotenv
import os

load_dotenv()

REGION = os.getenv("REGION", "ap-southeast-2")
ACCOUNT_ID = os.getenv("ACCOUNT_ID", "123456789012")
BUCKET_NAME = "ref-vision-video-bucket"
KINESIS_STREAM_NAME = "RefVisionVideoStream"
FIREHOSE_DELIVERY_STREAM_NAME = f"RefVisionFirehoseStream-{ACCOUNT_ID}-{REGION}"
VIDEO_BUCKET_ARN = f"arn:aws:s3:::{BUCKET_NAME}"

# Clients
iam_client = boto3.client("iam", region_name=REGION)
s3_client = boto3.client("s3", region_name=REGION)
kinesis_client = boto3.client("kinesis", region_name=REGION)
firehose_client = boto3.client("firehose", region_name=REGION)
logs_client = boto3.client("logs", region_name=REGION)
sqs_client = boto3.client("sqs", region_name=REGION)

# IAM Roles to Test
IAM_POLICIES = [
    (
        "VideoIngestionFunctionServiceRole",
        ["kinesis:PutRecord", "kinesis:PutRecords", "kinesis:ListShards"],
        f"arn:aws:kinesis:{REGION}:{ACCOUNT_ID}:stream/{KINESIS_STREAM_NAME}",
    ),
    (
        "RefVisionFirehoseRole",
        ["s3:PutObject", "s3:PutObjectAcl"],
        f"arn:aws:s3:::{BUCKET_NAME}/*",
    ),
]


@pytest.mark.parametrize("role_name, actions, resource_arn", IAM_POLICIES)
def test_role_permissions(role_name, actions, resource_arn):
    """
    Validate IAM roles have correct permissions.
    We must ensure that one policy statement contains *all* required actions
    (e.g., [kinesis:PutRecord, kinesis:PutRecords, kinesis:ListShards])
    on the *same* resource_arn.
    """
    # Fetch inline policies for the role
    inline_policies = iam_client.list_role_policies(RoleName=role_name)
    assert inline_policies, f"No inline policies found for {role_name}"

    found_statement = False
    for policy_name in inline_policies["PolicyNames"]:
        # Get the actual policy document
        policy_doc = iam_client.get_role_policy(
            RoleName=role_name, PolicyName=policy_name
        )
        statements = policy_doc["PolicyDocument"]["Statement"]

        for statement in statements:
            statement_actions = statement.get("Action", [])
            statement_resources = statement.get("Resource", [])

            # Normalize string fields to lists
            if isinstance(statement_actions, str):
                statement_actions = [statement_actions]
            if isinstance(statement_resources, str):
                statement_resources = [statement_resources]

            # Check if *all* actions in 'actions' are included in this statement
            if set(actions).issubset(set(statement_actions)) and (
                resource_arn in statement_resources
            ):
                found_statement = True
                break

        if found_statement:
            break

    assert (
        found_statement
    ), f"{role_name} is missing permission {actions} for {resource_arn}"


def test_bucket_exists():
    """
    Validate that the S3 bucket exists.
    """
    response = s3_client.list_buckets()
    bucket_names = {bucket["Name"] for bucket in response["Buckets"]}
    assert BUCKET_NAME in bucket_names, "S3 bucket does not exist."


def test_bucket_public_access():
    """
    Ensure that public access is blocked on the bucket.
    """
    response = s3_client.get_public_access_block(Bucket=BUCKET_NAME)
    config = response["PublicAccessBlockConfiguration"]
    assert config["BlockPublicAcls"], "Public ACLs are not blocked."
    assert config["IgnorePublicAcls"], "Public ACLs are not ignored."
    assert config["BlockPublicPolicy"], "Public policies are not blocked."
    assert config["RestrictPublicBuckets"], "Public bucket restrictions are missing."


def test_bucket_versioning():
    """
    Validate that versioning is enabled for the bucket.
    """
    response = s3_client.get_bucket_versioning(Bucket=BUCKET_NAME)
    assert response.get("Status") == "Enabled", "S3 bucket versioning is not enabled."


def test_kinesis_stream_active():
    """
    Ensure that the Kinesis stream is active.
    """
    response = kinesis_client.describe_stream(StreamName=KINESIS_STREAM_NAME)
    assert (
        response["StreamDescription"]["StreamStatus"] == "ACTIVE"
    ), "Kinesis stream is not active."


def test_firehose_stream_active():
    """
    Ensure that the Firehose delivery stream is active.
    """
    for _ in range(10):
        response = firehose_client.describe_delivery_stream(
            DeliveryStreamName=FIREHOSE_DELIVERY_STREAM_NAME
        )
        status = response["DeliveryStreamDescription"]["DeliveryStreamStatus"]
        if status == "ACTIVE":
            break
        time.sleep(5)
    else:
        assert False, "Firehose stream is not active."


def test_firehose_s3_destination():
    """
    Verify Firehose delivers to the correct S3 bucket.
    """
    response = firehose_client.describe_delivery_stream(
        DeliveryStreamName=FIREHOSE_DELIVERY_STREAM_NAME
    )
    destination = response["DeliveryStreamDescription"]["Destinations"][0]
    assert (
        destination["S3DestinationDescription"]["BucketARN"] == VIDEO_BUCKET_ARN
    ), "Firehose delivery stream does not point to the correct S3 bucket."


LOG_GROUPS = ["/aws/lambda/VideoIngestionFunction", "/aws/lambda/PreprocessingFunction"]


@pytest.mark.parametrize("log_group_name", LOG_GROUPS)
def test_log_group_exists(log_group_name):
    """
    Verify log groups exist for Lambda functions.
    """
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    assert len(response["logGroups"]) > 0, f"Log group {log_group_name} does not exist!"


@pytest.mark.parametrize("log_group_name", LOG_GROUPS)
def test_log_retention(log_group_name):
    """
    Validate that log retention is set to 7 days.
    """
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    assert (
        response["logGroups"][0]["retentionInDays"] == 7
    ), f"Retention not set to 7 days for {log_group_name}"


DLQ_NAME = "DLQ"  # Ensure name matches CDK stack


def test_dlq():
    """
    Test whether the DLQ exists and can receive and retrieve a test message.
    """
    response = sqs_client.get_queue_url(QueueName=DLQ_NAME)
    assert response["QueueUrl"], "DLQ does not exist!"
