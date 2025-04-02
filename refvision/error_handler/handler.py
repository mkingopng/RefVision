# refvision/error_handler/handler.py
"""
Module for handling errors in the RefVision pipeline.
"""

import logging
from typing import Optional
from refvision.dynamo_db.dynamodb_helpers import update_item

logger = logging.getLogger(__name__)


class RefVisionError(Exception):
    """
    Custom exception class for RefVision errors.
    """

    pass


def handle_error(
    meet_id: str,
    record_id: str,
    error: Exception,
    lifter_name: Optional[str] = None,
    status: str = "FAILED",
) -> None:
    """
    Handles an error by logging details, optionally updating DynamoDB with
    error info, and re-raising or swallowing the exception as needed.
    :param meet_id: Partition key in DynamoDB
    :param record_id: Sort key in DynamoDB
    :param error: The exception that occurred
    :param lifter_name: (Optional) Lifter name if relevant
    :param status: The new status to record in DynamoDB (e.g. "FAILED")
    :return: None
    """
    logger.error(
        f"Error encountered for MeetID={meet_id}, RecordID={record_id}: {error}"
    )

    # store the error message in DynamoDB:
    update_item(
        meet_id,
        record_id,
        {
            "Status": status,
            "ErrorMessage": str(error),
        },
    )
    # re-raise the exception or convert it to a RefVisionError:
    raise RefVisionError(f"RefVision Pipeline error => {error}") from error
