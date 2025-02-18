# tests/conftest.py
"""
This file is used to define fixtures that can be used in multiple test files.
"""
import pytest
import os
from dotenv import load_dotenv
import boto3

# Load environment variables from .env file
load_dotenv()


@pytest.fixture(scope="session", autouse=True)
def aws_credentials():
    """
    Load AWS credentials from environment variables
    :return:
    """
    os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID", "testing")
    os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY", "testing")
    os.environ["AWS_DEFAULT_REGION"] = os.getenv("AWS_DEFAULT_REGION", "ap-southeast-2")


@pytest.fixture(scope="function")
def s3_client():
    """
    Returns a real AWS S3 client
    :return:
    """
    return boto3.client("s3", region_name=os.getenv("AWS_DEFAULT_REGION"))


@pytest.fixture(scope="function")
def kinesis_client():
    """
    Returns a real AWS Kinesis client
    :return:
    """
    return boto3.client("kinesis", region_name=os.getenv("AWS_DEFAULT_REGION"))


@pytest.fixture(scope="function")
def firehose_client():
    """
    Returns a real AWS Firehose client
    :return:
    """
    return boto3.client("firehose", region_name=os.getenv("AWS_DEFAULT_REGION"))


@pytest.fixture(scope="function")
def dynamodb_client():
    """
    Returns a real AWS DynamoDB client
    :return:
    """
    return boto3.client("dynamodb", region_name=os.getenv("AWS_DEFAULT_REGION"))


@pytest.fixture(scope="function")
def lambda_client():
    """
    Returns a real AWS Lambda client
    :return:
    """
    return boto3.client("lambda", region_name=os.getenv("AWS_DEFAULT_REGION"))
