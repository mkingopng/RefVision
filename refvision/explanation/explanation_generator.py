# refvision/explanation/explanation_generator.py
"""
Generates a natural language explanation from a JSON decision using AWS Bedrock (Claude v2.1).
Supports both local and AWS DynamoDB environments.
"""
import os
import json
import boto3
import argparse
from botocore.exceptions import ClientError

# Set up Bedrock client
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
bedrock_runtime = boto3.client("bedrock-runtime", region_name=AWS_REGION)

# Detect if running in local mode
USE_LOCAL_DYNAMODB = os.getenv("USE_LOCAL_DYNAMODB", "False").lower() == "true"

# Set up DynamoDB client (local vs AWS)
if USE_LOCAL_DYNAMODB:
    dynamodb = boto3.resource("dynamodb", endpoint_url="http://localhost:8000")
else:
    dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table("PowerliftingMeet")


def load_prompt_template(filepath: str = "prompt_template.txt") -> str:
    """Load the prompt template from a file."""
    try:
        with open(filepath) as file:
            return file.read().strip()
    except FileNotFoundError:
        raise RuntimeError(f"Prompt template file '{filepath}' not found.")


def load_decision_json(filepath: str) -> dict:
    """Load decision JSON from a local file."""
    try:
        with open(filepath) as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Error loading decision JSON from {filepath}: {e}")


def load_decision_json_from_dynamodb(
    meet_id: str, lifter: str, attempt_number: int
) -> dict:
    """
    Load decision JSON from DynamoDB.
    :param meet_id: Powerlifting meet ID.
    :param lifter: Lifter's name or ID.
    :param attempt_number: Attempt number.
    :return: Decision JSON data as a dictionary.
    """
    try:
        response = table.get_item(
            Key={"meet_id": meet_id, "lifter": lifter, "attempt_number": attempt_number}
        )
        item = response.get("Item")
        if not item:
            raise ValueError(
                f"No decision found for {meet_id}, {lifter}, attempt {attempt_number}."
            )
        return item
    except ClientError as e:
        raise RuntimeError(f"DynamoDB retrieval error: {e}")


def store_decision_in_dynamodb(
    meet_id: str, lifter: str, attempt_number: int, explanation: str
):
    """
    Store or update the generated explanation in DynamoDB.
    """
    try:
        table.update_item(
            Key={
                "meet_id": meet_id,
                "lifter": lifter,
                "attempt_number": attempt_number,
            },
            UpdateExpression="SET explanation = :exp",
            ExpressionAttributeValues={":exp": explanation},
        )
    except ClientError as e:
        raise RuntimeError(f"DynamoDB storage error: {e}")


def generate_explanation(decision_data: dict, prompt_template_path: str) -> str:
    """
    Generate a natural language explanation from the decision
    JSON using AWS Bedrock.
    :param decision_data: The JSON decision data from the inference.
    :param prompt_template_path: The file path for the prompt template.
    :return: A natural language explanation.
    """

    # Load prompt template from a file
    try:
        with open(prompt_template_path) as f:
            prompt_template = f.read().strip()
    except FileNotFoundError:
        raise RuntimeError(f"Prompt template file '{prompt_template_path}' not found.")

    # Format JSON as part of the prompt
    formatted_decision = json.dumps(decision_data, indent=2)

    # construct full prompt
    prompt = prompt_template.replace("{decision_json}", formatted_decision)

    # define model parameters
    payload = {
        "prompt": prompt,
        "max_tokens_to_sample": 200,
        "temperature": 0.2,
        "top_p": 0.9,
    }

    try:
        # invoke AWS Bedrock
        response = bedrock_runtime.invoke_model(
            modelId="anthropic.claude-v2",  # Use the correct model
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload).encode(),
        )

        # parse response
        response_body = json.loads(response["body"].read())
        explanation = response_body.get("completion", "").strip()

        return explanation

    except ClientError as e:
        raise RuntimeError(f"Bedrock invocation error: {e}")


def handler(event, context=None):
    """
    AWS Lambda handler function to generate a natural language explanation.
    :param event: Lambda invocation event containing 'meet_id', 'lifter', 'attempt_number'.
    :param context: Lambda context (not used here).
    :return: Explanation string.
    """
    _ = context  # Unused
    meet_id = event.get("meet_id")
    lifter = event.get("lifter")
    attempt_number = event.get("attempt_number")

    if not meet_id or not lifter or attempt_number is None:
        raise ValueError("'meet_id', 'lifter', and 'attempt_number' must be provided.")

    prompt_template = load_prompt_template()
    decision_data = load_decision_json_from_dynamodb(meet_id, lifter, attempt_number)
    explanation = generate_explanation(decision_data, prompt_template)

    # Store explanation in DynamoDB
    decision_data["explanation"] = explanation
    store_decision_in_dynamodb(
        str(decision_data["meet_id"]),  # Ensure it's a string
        str(decision_data["lifter"]),  # Ensure it's a string
        int(decision_data["attempt_number"]),  # Ensure it's an int
        str(decision_data["explanation"]),  # Ensure it's a string
    )
    return {"statusCode": 200, "body": explanation}


def main(local: bool, lifter_info_path: str, inference_results_path: str):
    """
    Main function to execute explanation generation.
    :param inference_results_path:
    :param lifter_info_path:
    :param local: Whether to use local JSON files or DynamoDB.
    """
    prompt_template = load_prompt_template()

    if local:
        inference_json_path = "/tmp/inference_results.json"
        lifter_info_json_path = "/tmp/lifter_info.json"

        if not os.path.exists(inference_json_path) or not os.path.exists(
            lifter_info_json_path
        ):
            raise RuntimeError("Missing local JSON files for inference or lifter info.")
        with open(lifter_info_json_path) as f:
            lifter_info = json.load(f)
        with open(inference_json_path) as f:
            inference_results = json.load(f)

        decision_data = {**lifter_info, **inference_results}

    else:
        # Pull decision data directly from DynamoDB
        meet_id = os.getenv("MEET_ID")
        lifter = os.getenv("LIFTER")
        attempt_number = int(os.getenv("ATTEMPT_NUMBER", "1") or 1)

        if not meet_id or not lifter or attempt_number is None:
            raise ValueError(
                "MEET_ID, LIFTER, and ATTEMPT_NUMBER must be set in the environment."
            )

        decision_data = load_decision_json_from_dynamodb(
            meet_id, lifter, attempt_number
        )

    # Generate explanation
    explanation = generate_explanation(decision_data, prompt_template)

    # Store explanation in DynamoDB (cloud) or local file (debugging)
    decision_data["explanation"] = explanation

    if not local:
        store_decision_in_dynamodb(
            str(decision_data.get("meet_id", "")),
            str(decision_data.get("lifter", "")),
            int(decision_data.get("attempt_number", 0)),
            str(decision_data.get("explanation", "")),
        )
    else:
        with open("explanation_output.json", "w", encoding="utf-8") as outfile:
            json.dump(decision_data, outfile, indent=4)

    print("\nNatural Language Explanation:\n", explanation)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate explanation from decision JSON."
    )
    parser.add_argument(
        "--local", action="store_true", help="Use local JSON files instead of DynamoDB."
    )
    parser.add_argument(
        "--lifter_info_path",
        type=str,
        default="lifter_info.json",
        help="Path to lifter info JSON.",
    )
    parser.add_argument(
        "--inference_results_path",
        type=str,
        default="inference_results.json",
        help="Path to inference results JSON.",
    )
    args = parser.parse_args()
    main(args.local, args.lifter_info_path, args.inference_results_path)
