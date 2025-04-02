# refvision/scripts/run_pipeline.py
"""
RefVision Pipeline Runner
Steps:
    1) Convert raw input (MOV, etc.) to norm MP4 (no orientation metadata).
    2) YOLO inference -> produces an annotated .avi
    3) generate decision data
    4) Convert .avi -> .mp4
    4) Upload .mp4 to S3
    6) Launch Gunicorn to serve Flask on specified port.
Usage: poetry run python -m scripts.run_pipeline
"""

import argparse
import os
import sys
import json
from typing import List
from refvision.common.config_local import LocalConfig
from refvision.io.s3_upload import upload_file_to_s3
from refvision.utils.logging_setup import setup_logging
from refvision.io.s3_download import download_file_from_s3
from refvision.postprocess.convert import (
    normalize_video,
    convert_avi_to_mp4,
    run_command,
)
from refvision.web.launcher import launch_gunicorn
from refvision.common.config_base import CONFIG_YAML_PATH
from refvision.error_handler.handler import handle_error
import boto3


logger = setup_logging(os.path.join(os.path.dirname(__file__), "../logs/pipeline.log"))
config_path = CONFIG_YAML_PATH


def run_yolo_inference(video: str, model_path: str) -> None:
    """
    runs YOLO inference on the input .mp4 file → produces .avi (LocalConfig.AVI_OUTPUT)
    :param video:
    :param model_path:
    :return:
    """
    logger.info("=== YOLO Inference ===")
    cmd: List[str] = [
        "poetry",
        "run",
        "python",
        "-m",
        "refvision.inference.inference",
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
    :param video_s3_path: S3 path to the input video
    :param endpoint_name: Name of the SageMaker endpoint
    :param logger: Optional logger for logging information
    :return: JSON response from the SageMaker endpoint
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
    Orchestrates the RefVision pipeline:
      A) Download raw video from RAW_BUCKET/RAW_KEY
      B) Normalize to .mp4
      C) (Optional) upload normalized to NORMALIZED_BUCKET
      D) YOLO inference → ephemeral .avi
      E) Convert .avi → .mp4
      F) Upload final .mp4 to PROCESSED_BUCKET
      G) Read JSON decision
      H) Launch Gunicorn
    """
    parser = argparse.ArgumentParser(description="Orchestrate the RefVision pipeline")

    # optional overrides
    parser.add_argument("--raw-bucket", default=None)
    parser.add_argument("--raw-key", default=None)
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--flask-port", default=None)
    args = parser.parse_args()

    # example identifiers (for your DynamoDB or error logging):
    meet_id = "DEV_MEET_001"
    record_id = "DEV_LIFT_001"

    try:
        # 1) decide which bucket/key to pull from
        raw_bucket = args.raw_bucket or LocalConfig.RAW_BUCKET
        raw_key = args.raw_key or LocalConfig.RAW_KEY

        model_path = args.model_path or LocalConfig.MODEL_PATH
        flask_port = str(args.flask_port or LocalConfig.FLASK_PORT)

        # 2) download raw from S3 => local
        local_raw_path = os.path.join(LocalConfig.TEMP_DIR, os.path.basename(raw_key))
        download_file_from_s3(raw_bucket, raw_key, local_raw_path, logger=logger)

        # 3) normalize to .mp4
        normalized_mp4 = normalize_video(
            local_raw_path, LocalConfig.TEMP_DIR, logger=logger
        )

        # 3a) upload the normalized to S3
        upload_file_to_s3(
            normalized_mp4,
            LocalConfig.NORMALIZED_BUCKET,
            LocalConfig.NORMALIZED_KEY,
            logger=logger,
        )

        # 4) YOLO inference => ephemeral .avi in LocalConfig.AVI_OUTPUT
        run_yolo_inference(normalized_mp4, model_path)

        # 5) convert .avi => final .mp4
        convert_avi_to_mp4(
            LocalConfig.AVI_OUTPUT, LocalConfig.MP4_OUTPUT, logger=logger
        )

        # 6) upload final .mp4 to processed bucket
        upload_file_to_s3(
            LocalConfig.MP4_OUTPUT,
            LocalConfig.PROCESSED_BUCKET,
            LocalConfig.PROCESSED_KEY,
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
        launch_gunicorn(flask_port, logger=logger)

        # 9) remove local files
        os.remove(local_raw_path)
        os.remove(normalized_mp4)
        os.remove(LocalConfig.MP4_OUTPUT)

    except Exception as e:
        # if anything fails above, handle_error logs + optionally updates DynamoDB + re-raises
        handle_error(meet_id=meet_id, record_id=record_id, error=e)
        sys.exit(1)  # if you want to exit with error code


def main():
    local_pipeline()


if __name__ == "__main__":
    print("Running pipeline!")
    main()
    print("Pipeline complete!")

    #  todo: bedrock -> good explanation
    #  todo: DynamoDB -> store of state
    #  todo: Step Functions -> orchestration
    #  todo: serverless inference
