# refvision/orchestration/orchestrator.py
"""
Module to define and manage a Step Function or other workflow orchestration
for RefVision.
"""
import boto3
import os


def start_refvision_workflow(event_payload: dict) -> dict:
    """
    Starts the Step Functions state machine for the RefVision pipeline.
    :param event_payload: The input to the Step Function
    :return: The response from the Step Functions start_execution API
    """
    sf_client = boto3.client(
        "stepfunctions", region_name=os.getenv("AWS_REGION", "us-east-1")
    )
    state_machine_arn = os.getenv(
        "REFVISION_SF_ARN", "arn:aws:states:...:stateMachine:RefVisionPipeline"
    )

    response = sf_client.start_execution(
        stateMachineArn=state_machine_arn,
        input=str(event_payload),  # or json.dumps(event_payload)
    )
    return response


# todo: build this out
