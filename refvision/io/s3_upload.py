# refvision/io/s3_upload.py
"""
Module to upload files to S3.
"""
from typing import Optional
from refvision.io.s3_client import get_s3_client
import logging


def upload_file_to_s3(
    local_path: str,
    bucket: str,
    key: str,
    content_type: str = "video/mp4",
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Uploads a file from local_path to an S3 bucket with the given key.
    :param local_path: Path to the file on the local filesystem.
    :param bucket: Name of the S3 bucket to upload to.
    :param key: S3 key where the file will be stored.
    :param content_type: (Optional) Content-Type for S3 object, default is "video/mp4".
    :param logger: (Optional) Logger for logging progress messages.
    :return: None
    """
    s3_client = get_s3_client()
    if logger:
        logger.info(f"Uploading {local_path} => s3://{bucket}/{key}")
    s3_client.upload_file(
        local_path, bucket, key, ExtraArgs={"ContentType": content_type}
    )
    if logger:
        logger.info(f"Uploaded to s3://{bucket}/{key}")
