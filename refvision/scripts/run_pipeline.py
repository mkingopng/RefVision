# refvision/scripts/run_pipeline.py
"""
RefVision Pipeline Runner
Steps:
    1) store lifter_data JSON in DynamoDB
    2) If local-video was provided, upload it to S3 (simulate ingestion)
    3) decide which model path and port to use
    4) download raw from S3 => local
    5) normalise video to .mp4 with no metadata
    6) upload the normalised video to S3
    7) YOLO inference => ephemeral .avi in cfg["AVI_OUTPUT"]
    8) convert .avi => final .mp4
    9) upload final .mp4 to processed bucket
    10) read the decision from DynamoDB
    11) launch Gunicorn
    12) remove local files
"""

import argparse
import os
import sys
import json
from typing import Optional
import boto3
from refvision.common.config import get_config
from refvision.io.s3_upload import upload_file_to_s3
from refvision.io.s3_download import download_file_from_s3
from refvision.postprocess.convert import (
    normalize_video,
    convert_avi_to_mp4,
    run_command,
)
from refvision.web.launcher import launch_gunicorn
from refvision.error_handler.handler import handle_error
from refvision.utils.logging_setup import setup_logging
from refvision.dynamo_db.dynamodb_helpers import (
    create_item,
    get_item,
)

logger = setup_logging(os.path.join(os.path.dirname(__file__), "../logs/pipeline.log"))
cfg = get_config()


def run_yolo_inference(
    video: str, model_path: str, athlete_id: str, record_id: str
) -> None:
    """
    Runs YOLO inference on the provided video using the specified model path.
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
    run_command(cmd)


def run_inference_sagemaker(
    video_s3_path: str, endpoint_name: str, logger=None
) -> dict:
    """
    Invokes a SageMaker endpoint with the input video path, returning the
    decision.
    :param video_s3_path: S3 path to the input video.
    :param endpoint_name: Name of the SageMaker endpoint.
    :param logger: Optional logger for logging.
    :return: Inference result from the SageMaker endpoint.
    """
    sm_runtime = boto3.client("runtime.sagemaker")
    payload = {"video_s3_path": video_s3_path}
    if logger:
        logger.info(
            f"Invoking SageMaker endpoint={endpoint_name} with payload={payload}"
        )

    response = sm_runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType="application/json",
        Body=json.dumps(payload),
    )
    resp_body = response["Body"].read()
    result = json.loads(resp_body.decode("utf-8"))
    return result


def local_pipeline() -> None:
    """
    Orchestrates the RefVision pipeline.
    :return: None
    """
    lifter_data_json_path = os.path.join(
        cfg["PROJECT_ROOT"], "metadata", "lifter_metadata.json"
    )
    parser = argparse.ArgumentParser(description="Orchestrate the RefVision pipeline")

    # optional overrides
    parser.add_argument("--raw-bucket", default=None)
    parser.add_argument("--raw-key", default=None)
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--flask-port", default=None)

    # lifter data JSON
    parser.add_argument(
        "--lifter-data-json",
        default=None,
        help="Path to a local JSON file containing meet/athlete/lift details",
    )

    # local ingestion
    parser.add_argument(
        "--local-video",
        default=None,
        help="Path to a local .mov/.mp4 to simulate ingestion. Will be uploaded to raw bucket/key before processing.",
    )

    args = parser.parse_args()

    lifter_data: Optional[dict] = None

    try:
        # 1) store lifter_data JSON in DynamoDB
        if os.path.isfile(lifter_data_json_path):
            with open(lifter_data_json_path) as f:
                lifter_data = json.load(f)
            logger.info(f"Loaded lifter metadata from {lifter_data_json_path}")

        if lifter_data is not None:
            pk = lifter_data["athlete_ID"]
            sk = f"{lifter_data['lift']}#{lifter_data['attempt']}"

            create_item(
                meet_id=pk,
                record_id=sk,
                lifter_name=lifter_data["athlete_name"],
                lift=lifter_data["lift"],
                lift_number=int(lifter_data["attempt"]),
                metadata={"MeetName": lifter_data["meet_name"]},
            )
            logger.info(
                f"Created DynamoDB item for athlete={pk}, lift={lifter_data['lift']} attempt={lifter_data['attempt']}"
            )
        else:
            logger.warning("No lifter data JSON provided or file not found.")

        # 2) If local-video was provided, upload it to S3 (simulate ingestion)
        raw_bucket = args.raw_bucket or cfg["RAW_BUCKET"]
        raw_key = args.raw_key or cfg["RAW_KEY"]

        if args.local_video:
            logger.info(
                f"Simulating ingestion from local file: {args.local_video} => s3://{raw_bucket}/{raw_key}"
            )
            upload_file_to_s3(args.local_video, raw_bucket, raw_key, logger=logger)
            logger.info("Local ingestion complete.")

        # 3) decide which model path and port to use
        model_path = args.model_path or cfg["MODEL_PATH"]
        flask_port = str(args.flask_port or cfg["FLASK_PORT"])

        # 4) download raw from S3 => local
        local_raw_path = os.path.join(cfg["TEMP_DIR"], os.path.basename(raw_key))
        logger.info(f"Downloading from s3://{raw_bucket}/{raw_key} to {local_raw_path}")
        download_file_from_s3(raw_bucket, raw_key, local_raw_path, logger=logger)

        # 5) normalise video to .mp4 with no metadata
        normalized_mp4 = normalize_video(local_raw_path, cfg["TEMP_DIR"], logger=logger)

        # 6) upload the normalised video to S3
        upload_file_to_s3(
            normalized_mp4,
            cfg["NORMALIZED_BUCKET"],
            cfg["NORMALIZED_KEY"],
            logger=logger,
        )

        # 7) YOLO inference => ephemeral .avi in cfg["AVI_OUTPUT"]
        if lifter_data is not None:
            run_yolo_inference(
                normalized_mp4,
                model_path,
                athlete_id=lifter_data["athlete_ID"],
                record_id=f"{lifter_data['lift']}#{lifter_data['attempt']}",
            )
        else:
            logger.warning("No lifter data => skipping YOLO inference.")

        # 8) convert .avi => final .mp4
        convert_avi_to_mp4(cfg["AVI_OUTPUT"], cfg["MP4_OUTPUT"], logger=logger)

        # 9) upload final .mp4 to processed bucket
        upload_file_to_s3(
            cfg["MP4_OUTPUT"],
            cfg["PROCESSED_BUCKET"],
            cfg["PROCESSED_KEY"],
            logger=logger,
        )

        # 10) read the decision from DynamoDB
        # 10) read the decision from DynamoDB
        if lifter_data is not None:
            athlete_id = lifter_data["athlete_ID"]
            record_id = f"{lifter_data['lift']}#{lifter_data['attempt']}"
            item = get_item(athlete_id, record_id)

            if item:
                logger.info(f"Decision data => {item['InferenceResult']}")
            else:
                logger.warning(
                    "No inference result found in DynamoDB for this athlete/attempt."
                )

            os.environ["REFVISION_MEET_ID"] = athlete_id
            os.environ["REFVISION_RECORD_ID"] = record_id

            # 11) launch Gunicorn
            logger.info("Launching Gunicorn...")
            launch_gunicorn(flask_port, logger=logger)

            # 12) remove local files
            os.remove(local_raw_path)
            os.remove(normalized_mp4)
            os.remove(cfg["MP4_OUTPUT"])
            os.remove(cfg["TEMP_MP4_FILE"])
        else:
            # If lifter_data is None, skip these steps, or do something else
            logger.warning(
                "No lifter_data => skipping decision retrieval and Gunicorn launch."
            )

    except Exception as e:
        fallback_meet_id = "UNSET_MEET"
        fallback_record_id = "UNSET_RECORD"
        if lifter_data:
            fallback_meet_id = lifter_data["athlete_ID"]
            fallback_record_id = f"{lifter_data['lift']}#{lifter_data['attempt']}"
        handle_error(meet_id=fallback_meet_id, record_id=fallback_record_id, error=e)
        sys.exit(1)


def main():
    """
    Main entrypoint for the RefVision pipeline.
    :return:
    """
    print("Running pipeline!")
    local_pipeline()
    print("Pipeline complete!")


if __name__ == "__main__":
    main()
