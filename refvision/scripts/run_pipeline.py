# refvision/scripts/run_pipeline.py
"""
RefVision Pipeline Runner
Steps:
    0) (Optional) Simulate ingestion from a local .mov file to S3.
    1) Download raw input (MOV, etc.) from RAW_BUCKET/RAW_KEY
    2) Convert to norm MP4 (no orientation metadata).
    3) YOLO inference -> produces an annotated .avi
    4) generate decision data
    5) Convert .avi -> .mp4
    6) Upload .mp4 to S3
    7) Launch Gunicorn
Usage:
    poetry run python -m scripts.run_pipeline \
        --local-video path/to/local_file.mov
    or just
        poetry run python -m scripts.run_pipeline
    if you already have a file in S3.
"""

import argparse
import os
import sys
import json
from typing import List
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


logger = setup_logging(os.path.join(os.path.dirname(__file__), "../logs/pipeline.log"))
cfg = get_config()


def run_yolo_inference(video: str, model_path: str) -> None:
    """
    runs YOLO inference on the input .mp4 file → produces .avi (cfg["AVI_OUTPUT"])
    """
    logger.info("=== YOLO Inference ===")
    cmd: List[str] = [
        "poetry",
        "run",
        "python",
        "-m",
        "refvision.inference.local_inference",
        "--video",
        video,
        "--model_path",
        model_path,
    ]
    run_command(cmd)


def run_inference_sagemaker(
    video_s3_path: str, endpoint_name: str, logger=None
) -> dict:
    """
    Invokes a SageMaker endpoint with the input video path, returning the prediction/decision.
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
    """
    parser = argparse.ArgumentParser(description="Orchestrate the RefVision pipeline")

    # optional overrides
    parser.add_argument("--raw-bucket", default=None)
    parser.add_argument("--raw-key", default=None)
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--flask-port", default=None)
    # new argument for local ingestion
    parser.add_argument(
        "--local-video",
        default=None,
        help="Path to a local .mov/.mp4 to simulate ingestion. Will be uploaded to raw bucket/key before processing.",
    )
    args = parser.parse_args()

    # example identifiers (for your DynamoDB or error logging):
    meet_id = "DEV_MEET_001"
    record_id = "DEV_LIFT_001"

    try:
        # 0) If use --local-video, upload it to RAW_BUCKET/RAW_KEY
        raw_bucket = args.raw_bucket or cfg["RAW_BUCKET"]
        raw_key = args.raw_key or cfg["RAW_KEY"]

        if args.local_video:
            # Simulate ingestion: upload local file to s3
            logger.info(
                f"Simulating ingestion from local file: {args.local_video} => s3://{raw_bucket}/{raw_key}"
            )
            upload_file_to_s3(args.local_video, raw_bucket, raw_key, logger=logger)
            logger.info("Local ingestion complete.")

        # 1) decide which model path and port to use
        model_path = args.model_path or cfg["MODEL_PATH"]
        flask_port = str(args.flask_port or cfg["FLASK_PORT"])

        # 2) download raw from S3 => local
        local_raw_path = os.path.join(cfg["TEMP_DIR"], os.path.basename(raw_key))
        logger.info(f"Downloading from s3://{raw_bucket}/{raw_key} to {local_raw_path}")
        download_file_from_s3(raw_bucket, raw_key, local_raw_path, logger=logger)

        # 3) normalize to .mp4
        normalized_mp4 = normalize_video(local_raw_path, cfg["TEMP_DIR"], logger=logger)

        # 3a) upload the normalized to S3
        upload_file_to_s3(
            normalized_mp4,
            cfg["NORMALIZED_BUCKET"],
            cfg["NORMALIZED_KEY"],
            logger=logger,
        )

        # 4) YOLO inference => ephemeral .avi in cfg["AVI_OUTPUT"]
        run_yolo_inference(normalized_mp4, model_path)

        # 5) convert .avi => final .mp4
        convert_avi_to_mp4(cfg["AVI_OUTPUT"], cfg["MP4_OUTPUT"], logger=logger)

        # 6) upload final .mp4 to processed bucket
        upload_file_to_s3(
            cfg["MP4_OUTPUT"],
            cfg["PROCESSED_BUCKET"],
            cfg["PROCESSED_KEY"],
            logger=logger,
        )

        # 7) read the JSON decision file from inference
        inference_json_path = "/tmp/inference_results.json"
        if os.path.exists(inference_json_path):
            with open(inference_json_path) as f:
                decision_data = json.load(f)
            logger.info(f"Decision data => {decision_data}")
        else:
            logger.warning("No inference_results.json found; skipping decision data.")

        # 8) launch Gunicorn
        logger.info("Launching Gunicorn...")
        launch_gunicorn(flask_port, logger=logger)

        # 9) remove local files
        os.remove(local_raw_path)
        os.remove(normalized_mp4)
        os.remove(cfg["MP4_OUTPUT"])

    except Exception as e:
        handle_error(meet_id=meet_id, record_id=record_id, error=e)
        sys.exit(1)


def main():
    print("Running pipeline!")
    local_pipeline()
    print("Pipeline complete!")


if __name__ == "__main__":
    main()
