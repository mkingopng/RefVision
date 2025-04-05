# refvision/inference/inference_trigger.py
"""
This module triggers the inference process by starting a Step Functions state
machine execution when a new video is uploaded to the raw video bucket.

Environment Variables:
    STATE_MACHINE_ARN (str): The ARN of the Step Functions state machine to
    start.

Functions:
    handler(event: dict, context: object) -> dict:
        Lambda handler that logs the incoming event and starts the state
        machine execution if configured.
"""
import json
import logging
import os
from typing import Any, Dict
import boto3


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# retrieve the state machine ARN from the environment variables
STATE_MACHINE_ARN: str = os.environ.get("STATE_MACHINE_ARN", "")

# create a Step Functions client
sf_client = boto3.client("stepfunctions")


def handler(event: Dict[str, Any], context: object) -> Dict[str, Any]:
    """
    Lambda handler for triggering the inference process.
    :param event: (Dict[str, Any]) The event data that triggered the Lambda
    function.
    :param context: (object) The Lambda execution context.
    :returns: Dict[str, Any]: A dictionary containing the HTTP status code and
    a message.
    """
    logger.info("Received event: %s", json.dumps(event))

    if STATE_MACHINE_ARN:
        try:
            response = sf_client.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                input=json.dumps(event),  # transform or process the event as needed.
            )
            logger.info("Started state machine execution: %s", json.dumps(response))
        except Exception as e:
            logger.error("Error starting state machine execution: %s", e)
    else:
        logger.info("No state machine ARN provided; skipping execution.")

    return {"statusCode": 200, "body": json.dumps("Inference trigger processed.")}
