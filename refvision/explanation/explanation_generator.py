# refvision/explanation/explanation_generator.py
"""
Generates a natural language explanation from a JSON decision using AWS Bedrock (Claude v2.1).
"""
import json
import boto3
import argparse
from botocore.exceptions import ClientError

sort_key = ""


def load_prompt_template(filepath: str = "prompt_template.txt") -> str:
    """Load the prompt template from a file."""
    with open(filepath, "r") as file:
        return file.read()


def load_decision_json(filepath: str = "decision.json") -> dict:
    """Load decision JSON from file."""
    with open(filepath, "r") as file:
        return json.load(file)


def load_decision_json_from_dynamodb(
    lifter_id: str, lift_attempt: str, sort_key: str
) -> dict:
    """
    Load decision JSON from DynamoDB.
    :param lifter_id: ID of the lifter.
    :param lift_attempt: Specific lift attempt identifier.
    :return: JSON decision data as a dictionary.
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("RefVisionDecisions")
    sort_key = sort_key
    response = table.get_item(
        Key={
            "LifterID_LiftID": f"{lifter_id}_{lift_attempt}",
            "SortKey": sort_key,  # Adjust to actual sort key in DynamoDB
        }
    )
    item = response.get("Item")
    if not item:
        raise ValueError(
            f"No decision found for {lifter_id}_{lift_attempt} with sort key '{sort_key}'."
        )
    return item["decision_json"]


def generate_explanation(
    decision_json: dict,
    prompt_template: str,
    model_id: str = "anthropic.claude-v2",
    max_tokens: int = 200,
    temperature: float = 0.2,
    top_p: float = 0.9,
    region: str = "ap-southeast-2",
) -> str:
    """
    Generate natural language explanation from decision JSON using AWS Bedrock.
    :param region:
    :param decision_json: Decision data as dictionary.
    :param prompt_template: Template for the prompt with placeholder for decision_json.
    :param model_id: AWS Bedrock model ID.
    :param max_tokens: Max tokens for completion.
    :param temperature: Sampling temperature.
    :param top_p: Top_p parameter for sampling.
    :return: Natural language explanation.
    """
    bedrock_runtime = boto3.client("bedrock-runtime", region_name="ap-southeast-2")

    prompt = prompt_template.replace(
        "{decision_json}", json.dumps(decision_json, indent=2)
    )

    payload: dict[str, object] = {
        "prompt": prompt,
        "max_tokens_to_sample": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }

    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload).encode("utf-8"),
        )
        response_body = json.loads(response["body"].read())
        explanation: str = response_body.get("completion", "").strip()
        return explanation
    except ClientError as e:
        raise RuntimeError(f"Bedrock invocation error: {e}")


def handler(event, context):
    """
    AWS Lambda handler function to generate a natural language explanation.

    :param event: Lambda invocation event containing 'lifter_id', 'lift_attempt', and optional 'sort_key'.
    :param context: Lambda context (not used here).
    :return: Explanation string.
    """
    lifter_id = event.get("lifter_id")
    lift_attempt = event.get("lift_attempt")
    sort_key = event.get("sort_key", "")

    if not lifter_id or not lift_attempt:
        raise ValueError("'lifter_id' and 'lift_attempt' must be provided in event.")

    prompt_template = load_prompt_template()
    decision_json = load_decision_json_from_dynamodb(
        lifter_id=lifter_id, lift_attempt=lift_attempt, sort_key=sort_key
    )

    explanation = generate_explanation(decision_json, prompt_template)

    return {"statusCode": 200, "body": explanation}


def main(
    local: bool = True,
    lifter_id: str = "",
    lift_attempt: str = "",
    prompt_filepath: str = "prompt_template.txt",
) -> None:
    """
    Main function to execute explanation generation.
    :param local: Whether to use local decision JSON file or DynamoDB.
    :param lifter_id: Lifter's ID for DynamoDB lookup.
    :param lift_attempt: Lift attempt ID for DynamoDB lookup.
    :param prompt_filepath: File path for prompt template.
    """
    prompt_template = load_prompt_template(prompt_filepath)

    if local:
        decision_json = load_decision_json()
    else:
        if not lifter_id or not lift_attempt:
            raise ValueError(
                "lifter_id and lift_attempt must be provided in production mode."
            )
        decision_json = load_decision_json_from_dynamodb(
            lifter_id, lift_attempt, sort_key=sort_key
        )

    explanation = generate_explanation(decision_json, prompt_template)

    print("Natural Language Explanation:\n", explanation)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate explanations from decision JSON."
    )
    parser.add_argument("--local", type=bool, default=True, help="Use local JSON file.")
    parser = argparse.ArgumentParser(
        description="Generate explanation from decision JSON."
    )
    parser.add_argument(
        "--local",
        type=bool,
        default=True,
        help="Use local file (True) or DynamoDB (False)",
    )
    parser.add_argument(
        "--lifter_id", type=str, default="", help="Lifter ID for DynamoDB"
    )
    parser.add_argument(
        "--lift_attempt", type=str, default="", help="Lift attempt for DynamoDB"
    )
    args = parser.parse_args()

    main(local=args.local, lifter_id=args.lifter_id, lift_attempt=args.lift_attempt)
