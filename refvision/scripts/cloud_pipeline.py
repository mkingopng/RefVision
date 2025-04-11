# refvision/scripts/cloud_pipeline.py
"""
moving towards a full cloud pipeline
Steps:
    1) read then store lifter_metadata.json in DynamoDB
    2) check if local-video is mp4, H.264. if yes, use kvs to stream it and save to s3
    3) normalise video to .mp4 with no metadata using lambda if required
    4) download file from S3 => local for inference
    5) YOLO inference => ephemeral .avi in cfg["AVI_OUTPUT"]
    6) upload to s3 and convert .avi => final .mp4 using lambda
    7) upload decision to DynamoDB
    8) read the decision from DynamoDB
    9) pass decision and prompt to Bedrock
    10) save natural language explanation to DynamoDB
    11) launch Gunicorn and serve video, decision & natural language explanation
"""

import os
import json
import argparse

from refvision.dynamo_db.dynamodb_helpers import create_item, update_item, get_item
from refvision.io.s3_download import download_file_from_s3
from refvision.io.s3_upload import upload_file_to_s3
from refvision.inference.local_inference import run_inference


def is_h264_mp4(path: str) -> bool:
    """
    Quick check if a local file is already H.264 .mp4.
    Could run ffprobe or a simpler check.
    For demonstration only.
    """
    # TODO implement
    return False


def call_normalize_lambda(s3_input, s3_output):
    """
    Example placeholder function that calls a Lambda to do normalization.
    Adjust according to your actual Lambda invocation pattern.
    """
    # In reality, you'd do something like:
    #   lambda_client = boto3.client("lambda")
    #   response = lambda_client.invoke(
    #       FunctionName="YourNormalizeLambda",
    #       Payload=json.dumps({"input": s3_input, "output": s3_output})
    #   )
    #   ...
    print(f"Invoking Lambda to normalize from {s3_input} => {s3_output}")
    # simulate success
    return True


def call_convert_avi_lambda(s3_input, s3_output):
    """
    Another placeholder for a Lambda that converts .avi => .mp4, possibly using FFmpeg.
    """
    print(
        f"Invoking Lambda to convert .avi => .mp4. Input={s3_input}, Output={s3_output}"
    )
    return True


def call_bedrock_explanation(decision_json):
    """
    Placeholder call to bedrock.
    """
    # e.g. bedrock_runtime = boto3.client("bedrock-runtime", region_name="...")
    # bedrock_runtime.invoke_model(...)
    explanation_text = "Simulated explanation from Bedrock."
    return explanation_text


def main():
    parser = argparse.ArgumentParser(description="Cloud Pipeline for RefVision")
    parser.add_argument(
        "--lifter-data-json",
        default=None,
        help="Path to JSON containing meet/athlete/lift details",
    )
    parser.add_argument(
        "--local-video",
        default=None,
        help="Local path to .mov/.mp4 to simulate ingestion.",
    )
    parser.add_argument(
        "--bucket",
        default="refvision-raw-videos",
        help="S3 bucket for raw videos (or normalized videos).",
    )
    parser.add_argument(
        "--model-path", default=None, help="Local path to YOLO model if needed."
    )
    args = parser.parse_args()

    # 1) Read & store lifter_metadata.json in DynamoDB
    lifter_data = {}
    if args.lifter_data_json and os.path.isfile(args.lifter_data_json):
        with open(args.lifter_data_json) as f:
            lifter_data = json.load(f)
        meet_id = lifter_data.get("athlete_ID", "UnknownAthlete")
        record_id = (
            f"{lifter_data.get('lift','Squat')}#{lifter_data.get('attempt','1')}"
        )
        create_item(
            meet_id=meet_id,
            record_id=record_id,
            lifter_name=lifter_data.get("athlete_name", ""),
            lift=lifter_data.get("lift", "Squat"),
            lift_number=int(lifter_data.get("attempt", 1)),
            metadata={
                "MeetName": lifter_data.get("meet_name", ""),
                "Status": "PENDING",
            },
        )
        print(f"Created DynamoDB item => meet_id={meet_id}, record_id={record_id}")
    else:
        print("No lifter_data_json or file not found. Using defaults.")
        meet_id = "MEET001"
        record_id = "Squat#1"

    # 2) Check if local-video is mp4 H.264
    local_video = args.local_video
    if local_video and os.path.isfile(local_video):
        video_name = os.path.basename(local_video)
        if is_h264_mp4(local_video):
            # Then we can "stream" it to KVS, or simply upload to S3
            # For now, let's just upload it to S3
            upload_file_to_s3(local_video, args.bucket, video_name)
            # next we might trigger a function that pushes it to KVS, or an event
            print(f"Uploaded H.264 mp4 => s3://{args.bucket}/{video_name}")
            update_item(
                meet_id,
                record_id,
                {"Status": "UPLOADED", "VideoName": f"s3://{args.bucket}/{video_name}"},
            )
        else:
            # 3) normalise video using lambda if required
            # so first upload the raw file
            raw_key = f"raw/{video_name}"
            upload_file_to_s3(local_video, args.bucket, raw_key)
            # call our "normalize" lambda
            normalized_key = f"normalized/{os.path.splitext(video_name)[0]}.mp4"
            call_normalize_lambda(
                f"s3://{args.bucket}/{raw_key}", f"s3://{args.bucket}/{normalized_key}"
            )
            # update dynamo
            update_item(
                meet_id,
                record_id,
                {
                    "Status": "NORMALIZED",
                    "VideoName": f"s3://{args.bucket}/{normalized_key}",
                },
            )
            video_name = os.path.basename(normalized_key)

        # 4) Download from s3 => local for inference
        local_download_path = os.path.join("/tmp", video_name)
        download_file_from_s3(args.bucket, video_name, local_download_path)
        # 5) YOLO inference => ephemeral .avi
        model_path = args.model_path or "/path/to/yolo_model.pt"
        run_inference(
            video_file=local_download_path,
            model_path=model_path,
            athlete_id=meet_id,
            record_id=record_id,
        )

        # The local_inference might produce an .avi in cfg["AVI_OUTPUT"]
        avi_path = "/path/to/runs/pose/track/something.avi"  # you would get from config
        if os.path.exists(avi_path):
            # 6) upload to s3 + convert .avi => final .mp4 using lambda
            avi_key = f"processed/{os.path.basename(avi_path)}"
            upload_file_to_s3(avi_path, args.bucket, avi_key)
            final_mp4_key = (
                f"processed_final/{os.path.splitext(os.path.basename(avi_path))[0]}.mp4"
            )
            call_convert_avi_lambda(
                f"s3://{args.bucket}/{avi_key}", f"s3://{args.bucket}/{final_mp4_key}"
            )
            update_item(
                meet_id,
                record_id,
                {
                    "Status": "PROCESSED",
                    "ProcessedVideo": f"s3://{args.bucket}/{final_mp4_key}",
                },
            )
            print(f"Processed final .mp4 => s3://{args.bucket}/{final_mp4_key}")

        # 7) upload decision to DynamoDB (the local_inference already calls update_item with InferenceResult, but we could do more)
        # For demonstration:
        decision_data = {"Decision": "GOOD LIFT!", "Confidence": 0.95}
        update_item(
            meet_id, record_id, {"InferenceResult": decision_data, "Status": "DECIDED"}
        )

        # 8) read the decision from DynamoDB
        final_item = get_item(meet_id, record_id)
        print("Final DynamoDB item =>", final_item)

        # 9) pass decision + prompt to Bedrock
        bedrock_explanation = call_bedrock_explanation(
            final_item.get("InferenceResult", {})
        )

        # 10) save explanation to DynamoDB
        update_item(meet_id, record_id, {"ExplanationText": bedrock_explanation})

        # 11) launch Gunicorn to serve everything
        # e.g. os.system("gunicorn -w 2 -b 0.0.0.0:5000 refvision.web.flask_app:app")
        print("Launched Gunicorn (placeholder). Pipeline complete.")
    else:
        print("No local video provided or file not found => exiting.")


if __name__ == "__main__":
    main()
