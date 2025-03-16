# refvision/ingestion/lifter_data_ingestor.py
"""

"""
import json
from refvision.dynamodb.db_handler import store_data
import os


def ingest_lifter_data(lifter_info_path: str):
    """
    Reads lifter_info.json and stores the data in DynamoDB.
    :param lifter_info_path: Path to lifter info JSON file.
    """
    if not os.path.exists(lifter_info_path):
        raise FileNotFoundError(f"❌ ERROR: {lifter_info_path} does not exist.")

    with open(lifter_info_path) as f:
        lifter_data = json.load(f)

    meet_id = lifter_data.get("meet_id")
    lifter = lifter_data.get("lifter")
    attempt_number = lifter_data.get("attempt_number")

    if not meet_id or not lifter or attempt_number is None:
        raise ValueError(
            "❌ ERROR: 'meet_id', 'lifter', and 'attempt_number' must be provided."
        )

    store_data(meet_id, lifter, attempt_number, lifter_data)
    print(
        f"✅ Lifter data stored in DynamoDB: {meet_id}, {lifter}, Attempt {attempt_number}"
    )
