# tests/test_infra_advanced.py
"""
Advanced Infrastructure Tests for IAM, S3, Kinesis, Firehose, and Logs.

This updated test file filters for resources belonging to the RefVision project.
Adjust the filters (by name or tag) as needed.
"""
import boto3
import pytest
import time
from dotenv import load_dotenv
import os
from config.config import CFG

load_dotenv()

pytestmark = pytest.mark.skipif(
    CFG.FLASK_APP_MODE.lower() == "local",
    reason="Skipping AWS infra tests in local mode",
)

# Use the region and account from environment or defaults.
REGION = os.getenv("REGION", "ap-southeast-2")
ACCOUNT_ID = os.getenv("ACCOUNT_ID", "001499655372")

# Expected resource names (as created by our CDK stack)
BUCKET_NAME_1 = "refvision-raw-videos"
BUCKET_NAME_2 = "refvision-annotated-videos"
KINESIS_STREAM_NAME = "RefVisionVideoStream"
FIREHOSE_DELIVERY_STREAM_NAME = f"RefVisionFirehoseStream-{ACCOUNT_ID}-{REGION}"

# ARN formats
VIDEO_BUCKET_1_ARN = f"arn:aws:s3:::{BUCKET_NAME_1}"

# Clients
iam_client = boto3.client("iam", region_name=REGION)
s3_client = boto3.client("s3", region_name=REGION)
kinesis_client = boto3.client("kinesis", region_name=REGION)
firehose_client = boto3.client("firehose", region_name=REGION)
logs_client = boto3.client("logs", region_name=REGION)
sqs_client = boto3.client("sqs", region_name=REGION)


# Instead of listing inline policies (which may be empty), we define helper functions.
def get_role(role_name: str) -> dict:
    """Get IAM role details. Raises exception if not found."""
    return iam_client.get_role(RoleName=role_name)


# IAM Roles to Test – we now check that the roles exist and (if they have inline policies) that they contain the expected actions.
IAM_ROLES = {
    "VideoIngestionFunctionServiceRole": {
        "expected_actions": [
            "kinesis:PutRecord",
            "kinesis:PutRecords",
            "kinesis:ListShards",
        ],
        "resource_arn": f"arn:aws:kinesis:{REGION}:{ACCOUNT_ID}:stream/{KINESIS_STREAM_NAME}",
    },
    "RefVisionFirehoseRole": {
        "expected_actions": ["s3:PutObject", "s3:PutObjectAcl"],
        "resource_arn": f"arn:aws:s3:::{BUCKET_NAME_1}/*",
    },
}


@pytest.mark.parametrize("role_name,config", IAM_ROLES.items())
def test_role_exists_and_permissions(role_name: str, config: dict):
    """
    Validate that the IAM role exists and if it has inline policies,
    that at least one of them contains the expected actions on the specified resource ARN.
    """
    # Check that the role exists.
    role = get_role(role_name)
    assert role is not None, f"IAM role {role_name} does not exist."

    # Try to list inline policies. (It’s possible the role has no inline policies.)
    response = iam_client.list_role_policies(RoleName=role_name)
    policy_names = response.get("PolicyNames", [])
    if policy_names:
        found = False
        for pol in policy_names:
            policy_doc = iam_client.get_role_policy(RoleName=role_name, PolicyName=pol)
            statements = policy_doc["PolicyDocument"]["Statement"]
            # Ensure statements is a list.
            if not isinstance(statements, list):
                statements = [statements]
            for stmt in statements:
                actions = stmt.get("Action", [])
                if isinstance(actions, str):
                    actions = [actions]
                resources = stmt.get("Resource", [])
                if isinstance(resources, str):
                    resources = [resources]
                if set(config["expected_actions"]).issubset(set(actions)) and (
                    config["resource_arn"] in resources
                ):
                    found = True
                    break
            if found:
                break
        assert (
            found
        ), f"{role_name} is missing expected inline policy with actions {config['expected_actions']} on {config['resource_arn']}."
    else:
        # If no inline policies, simply pass (the role might use managed policies)
        pytest.skip(
            f"{role_name} has no inline policies; skipping inline policy check."
        )


def test_bucket_exists():
    """
    Validate that both S3 buckets exist by filtering for those with our expected names.
    """
    response = s3_client.list_buckets()
    bucket_names = {bucket["Name"] for bucket in response["Buckets"]}
    assert BUCKET_NAME_1 in bucket_names, f"S3 bucket {BUCKET_NAME_1} does not exist."
    assert BUCKET_NAME_2 in bucket_names, f"S3 bucket {BUCKET_NAME_2} does not exist."


def test_bucket_public_access():
    """
    Ensure that public access is blocked on bucket 1.
    """
    response = s3_client.get_public_access_block(Bucket=BUCKET_NAME_1)
    config = response["PublicAccessBlockConfiguration"]
    assert config["BlockPublicAcls"], "Public ACLs are not blocked on bucket 1."
    assert config["IgnorePublicAcls"], "Public ACLs are not ignored on bucket 1."
    assert config["BlockPublicPolicy"], "Public policies are not blocked on bucket 1."
    assert config[
        "RestrictPublicBuckets"
    ], "Public bucket restrictions are missing on bucket 1."


def test_bucket_versioning():
    """
    Validate that versioning is enabled for both buckets.
    """
    resp1 = s3_client.get_bucket_versioning(Bucket=BUCKET_NAME_1)
    resp2 = s3_client.get_bucket_versioning(Bucket=BUCKET_NAME_2)
    assert (
        resp1.get("Status") == "Enabled"
    ), f"S3 bucket {BUCKET_NAME_1} versioning is not enabled."
    assert (
        resp2.get("Status") == "Enabled"
    ), f"S3 bucket {BUCKET_NAME_2} versioning is not enabled."


def test_bucket_tags():
    """
    Validate that the buckets have at least the CloudFormation tag indicating they belong to our stack.
    """
    expected_key = "aws:cloudformation:stack-name"
    for bucket in [BUCKET_NAME_1, BUCKET_NAME_2]:
        try:
            response = s3_client.get_bucket_tagging(Bucket=bucket)
            tag_set = {tag["Key"]: tag["Value"] for tag in response["TagSet"]}
        except s3_client.exceptions.NoSuchBucket:
            pytest.skip(f"Bucket {bucket} does not exist.")
        except Exception:
            tag_set = {}
        assert (
            expected_key in tag_set
        ), f"Bucket {bucket} is missing tag {expected_key}."


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
        try:
            response = firehose_client.describe_delivery_stream(
                DeliveryStreamName=FIREHOSE_DELIVERY_STREAM_NAME
            )
            status = response["DeliveryStreamDescription"]["DeliveryStreamStatus"]
            if status == "ACTIVE":
                break
        except firehose_client.exceptions.ResourceNotFoundException:
            time.sleep(5)
    else:
        pytest.fail("Firehose stream is not active.")


def test_firehose_s3_destination():
    """
    Verify Firehose delivers to the correct S3 bucket.
    """
    response = firehose_client.describe_delivery_stream(
        DeliveryStreamName=FIREHOSE_DELIVERY_STREAM_NAME
    )
    destination = response["DeliveryStreamDescription"]["Destinations"][0]
    assert (
        destination["S3DestinationDescription"]["BucketARN"] == VIDEO_BUCKET_1_ARN
    ), "Firehose delivery stream does not point to the correct S3 bucket."


LOG_GROUPS = ["/aws/lambda/VideoIngestionFunction", "/aws/lambda/PreprocessingFunction"]


@pytest.mark.parametrize("log_group_name", LOG_GROUPS)
def test_log_group_exists(log_group_name: str):
    """
    Verify that log groups exist for the specified Lambda functions.
    """
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    assert (
        len(response.get("logGroups", [])) > 0
    ), f"Log group {log_group_name} does not exist!"


@pytest.mark.parametrize("log_group_name", LOG_GROUPS)
def test_log_retention(log_group_name: str):
    """
    Validate that log retention is set to 731 days for the specified log groups.
    """
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    groups = response.get("logGroups", [])
    if groups:
        retention = groups[0].get("retentionInDays")
        assert (
            retention == 731
        ), f"Retention not set to 731 days for {log_group_name}, found {retention}."
    else:
        pytest.skip(
            f"Log group {log_group_name} does not exist; skipping retention test."
        )


DLQ_NAME = "DLQ"  # Ensure this name matches the CDK stack


def test_dlq():
    """
    Test whether the DLQ exists.
    """
    try:
        response = sqs_client.get_queue_url(QueueName=DLQ_NAME)
        queue_url = response.get("QueueUrl")
        assert queue_url, "DLQ does not exist!"
    except sqs_client.exceptions.QueueDoesNotExist:
        pytest.fail("DLQ does not exist!")
