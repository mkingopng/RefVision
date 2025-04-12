# refvision/explanation/explanation_generator.py
"""
Generates a natural language explanation from a JSON decision using AWS Bedrock
  1) reads environment variables: MEET_ID, LIFTER_NAME, ATTEMPT_NUMBER
  2) retrieves the item from DynamoDB
  3) invokes the Claude 3 chat-based model via 'anthropic_version' structure
  4) saves the resulting text back into DynamoDB's ExplanationText
  5) prints the explanation to stdout
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


def load_decision_from_dynamodb(meet_id: str, record_id: str) -> dict:
    """
    Reads the item from DynamoDB with InferenceResult
    :param meet_id: The ID of the meet.
    :param lifter_name: The lifter's name.
    :return: The item retrieved from DynamoDB.
    """
    response = table.get_item(Key={"MeetID": meet_id, "RecordID": record_id})
    item = response.get("Item")
    if not item:
        raise ValueError(f"No item found in DynamoDB for {meet_id} / {record_id}")
    return convert_decimal_to_float(item)


def store_explanation_in_dynamodb(
    meet_id: str, record_id: str, explanation: str
) -> None:
    """
    Updates the ExplanationText field for the same item.
    :param meet_id: The ID of the meet.
    :param record_id:
    :param explanation: The generated explanation text.
    :return: None
    """
    table.update_item(
        Key={"MeetID": meet_id, "RecordID": record_id},
        UpdateExpression="SET ExplanationText = :exp",
        ExpressionAttributeValues={":exp": explanation},
    )


def invoke_claude_3_via_bedrock(prompt_text: str, max_tokens: int = 300) -> str:
    """
    Calls Bedrock model with a user message & decision numbers.
    Returns a natural language explanation.
    :param prompt_text: The prompt text to send to the model.
    :param max_tokens: The maximum number of tokens to generate.
    :return: The generated explanation text.
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
        print(json.dumps(response_body, indent=2))

        content_blocks = response_body.get("content", [])
        if not content_blocks:
            return "[No content returned by Claude-3]"

        final_text = []
        for block in content_blocks:
            if block.get("type") == "text":
                final_text.append(block.get("text", ""))

        joined_text = "\n".join(final_text).strip()
        return joined_text or "[No text found]"

    except ClientError as e:
        raise RuntimeError(f"Bedrock invocation error: {e}")


def main():
    """
    Main function to generate an explanation using AWS Bedrock.
    """
    meet_id = os.getenv("MEET_ID")
    record_id = os.getenv("RECORD_ID")  # "Theo Maddox#Squat#2"
    if not meet_id or not record_id:
        raise ValueError("Need MEET_ID and RECORD_ID environment variables.")

    item = load_decision_from_dynamodb(meet_id, record_id)

    inference_data = item.get("InferenceResult", {})
    prompt_text = (
        "Given the following JSON analysis of a powerlifting squat:\n\n"
        f"{json.dumps(inference_data, indent=2)}\n\n"
        "Create a concise explanation for powerlifting spectators..."
    )

    explanation = invoke_claude_3_via_bedrock(prompt_text)

    store_explanation_in_dynamodb(meet_id, record_id, explanation)

    print("Explanation from Claude-3:\n", explanation)


if __name__ == "__main__":
    main()
