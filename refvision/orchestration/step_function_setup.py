# refvision/orchestration/step_function_setup.py
"""
step function
"""
import boto3
import os

step_functions_client = boto3.client(
    "stepfunctions", region_name=os.getenv("AWS_DEFAULT_REGION")
)


def create_state_machine():
    """
    Deploys the Step Function for orchestrating RefVision.
    :return:
    """
    response = step_functions_client.create_state_machine(
        name="RefVisionWorkflow",
        definition="""
        {
            "Comment": "State machine for RefVision video processing",
            "StartAt": "Preprocess Video",
            "States": {
                "Preprocess Video": {
                    "Type": "Task",
                    "Resource": "arn:aws:lambda:...",
                    "End": true
                }
            }
        }
        """,
        roleArn=os.getenv("AWS_STEP_FUNCTION_ROLE"),
    )
    return response
