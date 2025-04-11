# refvision/ingestion/simulate_kvs.py
"""

"""

import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Simulate a camera feed by streaming a local video into Kinesis Video Streams using GStreamer."
    )
    parser.add_argument(
        "--video-file", required=True, help="Path to the local .mp4 video"
    )
    parser.add_argument(
        "--stream-name", required=True, help="Kinesis Video Stream name"
    )
    parser.add_argument("--region", default="ap-southeast-2", help="AWS region")
    parser.add_argument(
        "--log-level", default="4", help="GStreamer log level (0-6). Lower=more verbose"
    )

    args = parser.parse_args()

    # Example pipeline:
    # gst-launch-1.0 filesrc location=YourVideo.mp4 ! qtdemux ! h264parse ! kvssink stream-name=... aws-region=...
    #
    # If your MP4 is already H.264, you can do:
    #   filesrc ! qtdemux ! h264parse ! kvssink
    # If there's audio, you might add audio parse/encode steps or omit them.
    # If your video is not H.264, you might have to re-encode (like decodebin ! videoconvert ! x264enc).

    # For example (pure H.264), the pipeline might be:
    gst_cmd = [
        "gst-launch-1.0",
        "-v",  # verbose
        f"filesrc location={args.video_file}",
        "!",
        "qtdemux",
        "!",
        "h264parse",
        "!",
        f'kvssink stream-name="{args.stream_name}" aws-region="{args.region}"',
        f"log-config=kvssink:LOG_LEVEL_{args.log_level}",
    ]

    pipeline_str = " ".join(gst_cmd)
    print(f"Running GStreamer pipeline:\n{pipeline_str}\n")

    # We run GStreamer as a subprocess. If it fails, we exit with an error:
    try:
        subprocess.check_call(pipeline_str, shell=True)
    except subprocess.CalledProcessError as e:
        print(
            f"Error: GStreamer pipeline failed with return code {e.returncode}",
            file=sys.stderr,
        )
        sys.exit(e.returncode)

    print("Done streaming to Kinesis Video Streams.")


if __name__ == "__main__":
    main()
