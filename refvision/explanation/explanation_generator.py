# refvision/explanation/explanation_generator.py
"""
Generates a natural language explanation from a JSON decision using AWS Bedrock
(Claude 3 haiku). It:
  1) Reads environment variables: MEET_ID, LIFTER, ATTEMPT_NUMBER
  2) Retrieves the item from DynamoDB
  3) Invokes the Claude 3 chat-based model via 'anthropic_version' structure
  4) Saves the resulting text back into DynamoDB's ExplanationText
  5) Prints the explanation to stdout
"""

import os
import json
import boto3
from botocore.exceptions import ClientError

from refvision.dynamo_db.dynamodb_helpers import convert_decimal_to_float

AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE", "StateStore")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
bedrock_runtime = boto3.client("bedrock-runtime", region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

ANTHROPIC_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"


def load_decision_from_dynamodb(meet_id: str, lifter: str, attempt_number: int) -> dict:
    """
    Reads the item from DynamoDB with InferenceResult, etc.
    Key: {MeetID: <meet_id>, RecordID: <lifter>#{attempt_number}}.
    Returns a dictionary with 'metadata', 'inference_results', etc.
    """
    record_id = f"{lifter}#{attempt_number}"
    try:
        response = table.get_item(Key={"MeetID": meet_id, "RecordID": record_id})
        item = response.get("Item")
        if not item:
            raise ValueError(f"No item found in DynamoDB for {meet_id} / {record_id}")
        return convert_decimal_to_float(item)

    except ClientError as e:
        raise RuntimeError(f"DynamoDB retrieval error: {e}")


def store_explanation_in_dynamodb(
    meet_id: str, lifter: str, attempt_number: int, explanation: str
) -> None:
    """
    Updates the ExplanationText field for the same item.
    :param meet_id: The ID of the meet.
    :param lifter: The lifter's name.
    :param attempt_number: The attempt number.
    :param explanation: The generated explanation text.
    :return: None
    """
    record_id = f"{lifter}#{attempt_number}"
    try:
        table.update_item(
            Key={"MeetID": meet_id, "RecordID": record_id},
            UpdateExpression="SET ExplanationText = :exp",
            ExpressionAttributeValues={":exp": explanation},
        )
    except ClientError as e:
        raise RuntimeError(f"DynamoDB update error: {e}")


def invoke_claude_3_via_bedrock(prompt_text: str, max_tokens: int = 300) -> str:
    """
    Calls the Bedrock 'anthropic.claude-3-haiku-20240307-v1:0' with a single user message.
    Note that we do NOT pass 'role': 'system' because the Anthropic Bedrock schema does
    not allow that role. We only provide 'role': 'user' in our 'messages' array.
    """
    try:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": prompt_text}]}
            ],
        }

        response = bedrock_runtime.invoke_model(
            modelId=ANTHROPIC_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body).encode(),
        )

        response_body = json.loads(response["body"].read())

        print("DEBUG: Full Bedrock response body:")
        print(response_body)
        print(json.dumps(response_body, indent=2))

        completion_text = response_body.get("completion")
        if not completion_text:
            return "[No completion returned by Claude-3]"

        return completion_text.strip()

    except ClientError as e:
        raise RuntimeError(f"Bedrock invocation error: {e}")


def main():
    """
    1) Pull environment variables: MEET_ID, LIFTER, ATTEMPT_NUMBER
    2) Get the item from DynamoDB => includes 'InferenceResult'
    3) Convert it to float (since it has Decimals)
    4) Craft a 'prompt_text' from that data
    5) Call the anthropic claude endpoint
    6) Save to DynamoDB and print.
    """
    meet_id = os.getenv("MEET_ID")
    lifter = os.getenv("LIFTER")
    attempt_str = os.getenv("ATTEMPT_NUMBER")

    if not meet_id or not lifter or not attempt_str:
        raise ValueError("Need MEET_ID, LIFTER, ATTEMPT_NUMBER environment variables.")

    attempt_number = int(attempt_str)
    item = load_decision_from_dynamodb(meet_id, lifter, attempt_number)

    item_float = convert_decimal_to_float(item)

    inference_data = item_float.get("InferenceResult", {})

    prompt_text = (
        "Given the following JSON analysis of a powerlifting squat:\n\n"
        f"{json.dumps(inference_data, indent=2)}\n\n"
        "Create a concise explanation for powerlifting spectators. "
        "Clearly state whether the squat was successful, and reference the numeric difference between hip and knee.\n"
    )

    explanation = invoke_claude_3_via_bedrock(prompt_text)

    store_explanation_in_dynamodb(meet_id, lifter, attempt_number, explanation)

    print("Explanation from Claude-3:\n", explanation)


if __name__ == "__main__":
    main()
