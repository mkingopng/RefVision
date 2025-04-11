# refvision/scripts/run_pipeline.py
"""
RefVision Pipeline Runner for local inference.
Steps:
 1) Load & store lifter_data JSON in DynamoDB
 2) Upload local raw video => S3
 3) Decide model path & Flask port
 4) Download raw from S3 => local
 5) Normalize video => H.264 MP4
 6) Upload normalized .mp4 => S3
 7) YOLO inference => ephemeral .avi
 8) Convert .avi => final .mp4
 9) Upload final .mp4 => processed bucket
10) Read the decision from DynamoDB
11) Generate explanation via Bedrock
12) Launch Gunicorn
13) Remove local files
"""

import argparse
import os
import sys
import json
from refvision.common.config import get_config
from refvision.io.s3_upload import upload_file_to_s3
from refvision.io.s3_download import download_file_from_s3
from refvision.postprocess.convert import (
    normalize_video,
    convert_avi_to_mp4,
    run_command,
)
from refvision.dynamo_db.dynamodb_helpers import create_item, get_item
from refvision.web.launcher import launch_gunicorn
from refvision.error_handler.handler import handle_error
from refvision.utils.logging_setup import setup_logging

logger = setup_logging(os.path.join(os.path.dirname(__file__), "../logs/pipeline.log"))
cfg = get_config()

# resolve absolute paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))
PROMPT_PATH = os.path.join(SCRIPT_DIR, "prompt_template.txt")


def load_prompt_template(filepath: str = PROMPT_PATH) -> str:
    """
    Loads the prompt template from a file.
    :param filepath: Path to the prompt template file.
    :return: The content of the prompt template.
    """
    with open(filepath) as f:
        return f.read().strip()


def run_yolo_inference(
    video: str, model_path: str, athlete_id: str, record_id: str
) -> None:
    """
    Runs YOLO inference on the provided video using the specified model path
    :param video: Path to the input video file.
    :param model_path: Path to the YOLO model.
    :param athlete_id: Athlete ID for the inference.
    :param record_id: Record ID for the inference.
    :return: None
    """
    logger.info("=== YOLO Inference ===")
    cmd = [
        "poetry",
        "run",
        "python",
        "-m",
        "refvision.inference.local_inference",
        "--video",
        video,
        "--model_path",
        model_path,
        "--athlete_id",
        athlete_id,
        "--record_id",
        record_id,
    ]
    run_command(cmd, logger=logger)


def generate_explanation_via_bedrock(meet_id: str, record_id: str) -> None:
    """
    Generates an explanation using AWS Bedrock.
    :param meet_id: The ID of the meet.
    :param record_id: The record ID for the lifter.
    :return: None
    """
    logger.info("=== Generating explanation via Bedrock ===")
    os.environ["MEET_ID"] = meet_id

    if "#" in record_id:
        (lift_type, attempt_number) = record_id.split("#", 1)
    else:
        lift_type, attempt_number = record_id, "1"

    os.environ["LIFTER"] = lift_type
    os.environ["ATTEMPT_NUMBER"] = attempt_number

    cmd = [
        "poetry",
        "run",
        "python",
        "-m",
        "refvision.explanation.explanation_generator",
    ]
    run_command(cmd, logger=logger)


def local_pipeline():
    """
    Local pipeline orchestration for RefVision.
    """
    parser = argparse.ArgumentParser(
        description="Orchestrate the RefVision pipeline (local)."
    )
    parser.add_argument("--raw-bucket", default=None)
    parser.add_argument("--raw-key", default=None)
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--flask-port", default=None)
    args = parser.parse_args()

    lifter_data = None
    try:
        # 1) load lifter_data JSON & store in DynamoDB
        metadata_json_path = cfg.get("LIFTER_METADATA_JSON")
        if not metadata_json_path or not os.path.isfile(metadata_json_path):
            raise FileNotFoundError(
                f"Mandatory lifter metadata file not found: {metadata_json_path}"
            )

        with open(metadata_json_path, encoding="utf-8") as f:
            lifter_data = json.load(f)

        meet_id = lifter_data["meet_name"]
        athlete_id = lifter_data["athlete_ID"]
        record_id = f"{lifter_data['lift']}#{lifter_data['attempt']}"
        lifter_name = lifter_data["athlete_name"]

        create_item(
            meet_id=meet_id,
            record_id=record_id,
            lifter_name=lifter_name,
            lift=lifter_data["lift"],
            lift_number=int(lifter_data["attempt"]),
            metadata=lifter_data,
        )
        logger.info(
            f"Created DynamoDB item => athlete={athlete_id}, record={record_id}"
        )

        # 2) local raw video => S3
        local_raw_video = cfg.get("LOCAL_RAW_VIDEO")
        if not local_raw_video or not os.path.isfile(local_raw_video):
            raise FileNotFoundError(
                f"Mandatory local raw video file not found: {local_raw_video}"
            )

        raw_bucket = args.raw_bucket or cfg["RAW_BUCKET"]
        raw_key = args.raw_key or cfg["RAW_KEY"]
        logger.info(f"Uploading local raw video => s3://{raw_bucket}/{raw_key}")
        upload_file_to_s3(local_raw_video, raw_bucket, raw_key, logger=logger)

        # 3) model path & Flask port
        model_path = args.model_path or cfg["MODEL_PATH"]
        flask_port = str(args.flask_port or cfg["FLASK_PORT"])

        # 4) download raw from S3 => local
        local_raw_path = os.path.join(cfg["TEMP_DIR"], os.path.basename(raw_key))
        logger.info(f"Downloading from s3://{raw_bucket}/{raw_key} => {local_raw_path}")
        download_file_from_s3(raw_bucket, raw_key, local_raw_path, logger=logger)

        # 5) normalise video => H.264 MP4
        normalized_mp4 = normalize_video(
            local_raw_path, cfg["OUTPUT_DIR"], logger=logger
        )

        # 6) upload the normalised .mp4 => S3
        upload_file_to_s3(
            normalized_mp4,
            cfg["NORMALIZED_BUCKET"],
            cfg["NORMALIZED_KEY"],
            logger=logger,
        )

        # 7) YOLO inference => ephemeral .avi
        run_yolo_inference(
            normalized_mp4,
            model_path,
            athlete_id=athlete_id,
            record_id=record_id,
        )

        # 8) convert .avi => final .mp4
        convert_avi_to_mp4(cfg["AVI_OUTPUT"], cfg["MP4_OUTPUT"], logger=logger)

        # 9) upload final .mp4 => processed bucket
        upload_file_to_s3(
            cfg["MP4_OUTPUT"],
            cfg["PROCESSED_BUCKET"],
            cfg["PROCESSED_KEY"],
            logger=logger,
        )

        # 10) read the decision from DynamoDB
        item = get_item(athlete_id, record_id)
        if item and "InferenceResult" in item:
            logger.info(f"InferenceResult => {item['InferenceResult']}")
        else:
            logger.warning("No inf result found in DynamoDB for this athlete/attempt")

        # 11) generate explanation via Bedrock
        if item:
            meet_id = item["MeetID"]
            generate_explanation_via_bedrock(meet_id, record_id)
        else:
            logger.warning("No item => skipping explanation generation step.")

        # 12) launch Gunicorn
        logger.info(f"Launching Gunicorn on port={flask_port}...")
        launch_gunicorn(flask_port, logger=logger)

        # 13) remove local files
        logger.info("Cleaning up local artifacts...")
        os.remove(local_raw_path)
        os.remove(normalized_mp4)
        os.remove(cfg["MP4_OUTPUT"])
        if os.path.exists(cfg["TEMP_MP4_FILE"]):
            os.remove(cfg["TEMP_MP4_FILE"])

    except Exception as e:
        fallback_meet_id = "UNKNOWN_MEET"
        fallback_record_id = "UNKNOWN_RECORD"
        if lifter_data:
            fallback_meet_id = lifter_data.get("athlete_ID", fallback_meet_id)
            fallback_record_id = f"{lifter_data['lift']}#{lifter_data['attempt']}"
        handle_error(meet_id=fallback_meet_id, record_id=fallback_record_id, error=e)
        sys.exit(1)


def main():
    """
    Main function to run the RefVision pipeline.
    """
    print("Starting pipeline")
    local_pipeline()
    print("Pipeline complete!")


if __name__ == "__main__":
    main()
