#
"""

"""
import boto3
import pytest

# Initialize AWS clients
logs_client = boto3.client('logs')
sqs_client = boto3.client('sqs')

# Environment configurations for tests
LAMBDA_FUNCTIONS = [
    ("VideoIngestionFunction", 7),
    ("PreprocessingFunction", 7)
]
DLQ_NAME = "DLQ"
TEST_MESSAGE = "Test DLQ message"

@pytest.mark.parametrize("function_name, expected_retention", LAMBDA_FUNCTIONS)
def test_cloudwatch_log_group(function_name, expected_retention):
    """
    Test whether CloudWatch log groups exist and have the expected retention period.

    Args:
        function_name (str): Name of the Lambda function.
        expected_retention (int): Expected retention period in days.
    """
    log_group_name = f"/aws/lambda/{function_name}"
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)

    # Check if the log group exists
    assert response['logGroups'], f"Log group {log_group_name} not found."

    # Validate retention period
    retention_days = response['logGroups'][0].get('retentionInDays')
    assert retention_days == expected_retention, (
        f"Log group {log_group_name} retention is {retention_days} days, expected {expected_retention}."
    )


def test_dlq():
    """
    Test whether the DLQ exists and can receive and retrieve a test message.
    """
    # Get the queue URL
    response = sqs_client.get_queue_url(QueueName=DLQ_NAME)
    queue_url = response['QueueUrl']

    # Send a test message
    sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=TEST_MESSAGE
    )

    # Receive the message
    messages = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=2
    )

    # Check if the message is in the queue
    assert 'Messages' in messages, f"DLQ {DLQ_NAME} did not receive the test message."

    # Cleanup the message from the queue
    receipt_handle = messages['Messages'][0]['ReceiptHandle']
    sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)


if __name__ == "__main__":
    pytest.main()
