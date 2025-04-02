# refvision/io/s3_download.py
"""
Module to download files from S3.
"""
from typing import Optional
import logging
from refvision.utils.aws_clients import get_s3_client


def download_file_from_s3(
    bucket: str, key: str, local_path: str, logger: Optional[logging.Logger] = None
) -> None:
    """
    Downloads a file from an S3 bucket to a local path.
    :param bucket: Name of the S3 bucket.
    :param key: Key of the file in S3.
    :param local_path: Path where the file should be saved locally.
    :param logger: (Optional) Logger for logging progress messages.
    :return: None
    """
    s3 = get_s3_client()
    if logger:
        logger.info(f"Downloading s3://{bucket}/{key} to {local_path}")
    s3.download_file(bucket, key, local_path)
    if logger:
        logger.info(f"Downloaded s3://{bucket}/{key} => {local_path}")
