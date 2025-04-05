# refvision/utils/aws_clients.py
"""

"""
import boto3


def get_dynamodb_client():
    """Returns a real AWS DynamoDB client"""
    return boto3.client("dynamodb")


def get_kinesis_client():
    """Returns a real AWS Kinesis client"""
    return boto3.client("kinesis")


def get_firehose_client():
    """Returns a real AWS Firehose client"""
    return boto3.client("firehose")


def get_lambda_client():
    """Returns a real AWS Lambda client"""
    return boto3.client("lambda")
