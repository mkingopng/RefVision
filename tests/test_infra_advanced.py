# tests/test_infra_advanced.py
"""
Advanced Infrastructure Tests for IAM, S3, Kinesis, and Firehose.
"""
import boto3
import pytest
import time
import json
from dotenv import load_dotenv
import os

load_dotenv()

# -------------------------------------------
# Environment Variables and Setup
# -------------------------------------------
REGION = os.getenv('REGION', 'ap-southeast-2')
ACCOUNT_ID = os.getenv('ACCOUNT_ID', '123456789012')
BUCKET_NAME = "ref-vision-video-bucket"
KINESIS_STREAM_NAME = "RefVisionVideoStream"
FIREHOSE_DELIVERY_STREAM_NAME = f"RefVisionFirehoseStream-{ACCOUNT_ID}-{REGION}"
VIDEO_BUCKET_ARN = f"arn:aws:s3:::{BUCKET_NAME}"

# Clients
iam_client = boto3.client('iam', region_name=REGION)
s3_client = boto3.client('s3', region_name=REGION)
kinesis_client = boto3.client('kinesis', region_name=REGION)
firehose_client = boto3.client('firehose', region_name=REGION)
logs_client = boto3.client('logs', region_name=REGION)

# IAM Roles to Test
IAM_POLICIES = [
    (
        "VideoIngestionFunctionServiceRole",
        ["kinesis:PutRecord", "kinesis:PutRecords", "kinesis:ListShards"],
        f"arn:aws:kinesis:{REGION}:{ACCOUNT_ID}:stream/{KINESIS_STREAM_NAME}"
    ),
    (
        "RefVisionFirehoseRole",
        ["s3:PutObject", "s3:PutObjectAcl"],
        f"arn:aws:s3:::{BUCKET_NAME}/*"
    ),
    (
        "BucketCleanupFunctionServiceRole",
        ["s3:ListBucket", "s3:ListBucketVersions", "s3:DeleteObject", "s3:DeleteObjectVersion"],
        f"arn:aws:s3:::{BUCKET_NAME}/*"
    )
]

# -------------------------------------------
# IAM Role Tests
# -------------------------------------------

@pytest.mark.parametrize("role_name, actions, resource_arn", IAM_POLICIES)
def test_role_permissions(role_name, actions, resource_arn):
    """
    Validate IAM roles have correct permissions.
    """
    # Inline policies
    inline_policies = iam_client.list_role_policies(RoleName=role_name)
    assert inline_policies, f"No inline policies found for {role_name}"

    # Validate permissions
    for policy_name in inline_policies['PolicyNames']:
        policy_doc = iam_client.get_role_policy(
            RoleName=role_name,
            PolicyName=policy_name
        )
        statements = policy_doc["PolicyDocument"]["Statement"]
        for statement in statements:
            statement_actions = statement.get("Action", [])
            statement_resources = statement.get("Resource", [])
            if isinstance(statement_actions, str):
                statement_actions = [statement_actions]
            if isinstance(statement_resources, str):
                statement_resources = [statement_resources]

            for action in actions:
                if action in statement_actions and resource_arn in statement_resources:
                    break
            else:
                assert False, f"{role_name} is missing permission {actions} for {resource_arn}"


# -------------------------------------------
# S3 Bucket Tests
# -------------------------------------------

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


# -------------------------------------------
# Kinesis and Firehose Validation Tests
# -------------------------------------------

def test_kinesis_stream_active():
    """
    Ensure that the Kinesis stream is active.
    """
    response = kinesis_client.describe_stream(StreamName=KINESIS_STREAM_NAME)
    assert response["StreamDescription"]["StreamStatus"] == "ACTIVE", "Kinesis stream is not active."


def test_firehose_stream_active():
    """
    Ensure that the Firehose delivery stream is active.
    """
    for _ in range(10):
        response = firehose_client.describe_delivery_stream(
            DeliveryStreamName=FIREHOSE_DELIVERY_STREAM_NAME)
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
    destination = response['DeliveryStreamDescription']['Destinations'][0]
    assert destination['S3DestinationDescription']['BucketARN'] == VIDEO_BUCKET_ARN, \
        "Firehose delivery stream does not point to the correct S3 bucket."


# -------------------------------------------
# Cleanup Tests
# -------------------------------------------

def test_cleanup_function_execution():
    """
    Verify cleanup Lambda removes files from the bucket.
    """
    # Upload a test file
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key="test_file.txt",
        Body="This is a test file."
    )

    # Destroy the stack (manual execution for now)
    os.system("cdk destroy --force")

    # Validate cleanup
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        assert "Contents" not in response, "Bucket still contains objects after cleanup!"
    except Exception as e:
        assert "NoSuchBucket" in str(e), "Bucket was not deleted properly!"


# -------------------------------------------
# Log Group Tests
# -------------------------------------------

LOG_GROUPS = [
    f"/aws/lambda/VideoIngestionFunction",
    f"/aws/lambda/PreprocessingFunction"
]


@pytest.mark.parametrize("log_group_name", LOG_GROUPS)
def test_log_group_exists(log_group_name):
    """
    Verify log groups exist for Lambda functions.
    """
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    assert len(response['logGroups']) > 0, f"Log group {log_group_name} does not exist!"


@pytest.mark.parametrize("log_group_name", LOG_GROUPS)
def test_log_retention(log_group_name):
    """
    Validate that log retention is set to 7 days.
    """
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    assert response['logGroups'][0]['retentionInDays'] == 7, f"Retention not set to 7 days for {log_group_name}"


# -------------------------------------------
# Final Tests and Cleanup
# -------------------------------------------

@pytest.fixture(scope="module")
def cleanup_s3():
    """
    Cleanup S3 test data after tests are executed.
    """
    yield
    objects = s3_client.list_objects_v2(Bucket=BUCKET_NAME).get('Contents', [])
    for obj in objects:
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=obj['Key'])


if __name__ == "__main__":
    pytest.main()
