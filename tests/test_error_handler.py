# tests/test_error_handler.py
"""
test the error handler module
"""

import pytest
from unittest.mock import patch
from refvision.error_handler.handler import handle_error, RefVisionError


def test_handle_error_updates_dynamodb_and_raises():
    """
    Ensures that handle_error:
      1) calls update_item with Status=FAILED and the error message
      2) raises a RefVisionError (chaining the original Exception)
    """
    with patch("refvision.error_handler.handler.update_item") as mock_update:
        meet_id = "TestMeet"
        record_id = "Alice#Squat#1"
        original_error = Exception("Something went wrong")

        # we expect handle_error to raise RefVisionError
        with pytest.raises(RefVisionError) as exc_info:
            handle_error(meet_id=meet_id, record_id=record_id, error=original_error)

        # check the call to update_item
        mock_update.assert_called_once_with(
            meet_id,
            record_id,
            {
                "Status": "FAILED",
                "ErrorMessage": "Something went wrong",
            },
        )

        # ensure the final raised exception includes the original error message
        raised_exc = exc_info.value
        assert "Something went wrong" in str(raised_exc)
        assert "RefVision Pipeline error => Something went wrong" in str(raised_exc)


def test_handle_error_custom_status():
    """
    If we pass a custom status, handle_error should store it in DynamoDB
    but still raise RefVisionError.
    """
    with patch("refvision.error_handler.handler.update_item") as mock_update:
        meet_id = "TestMeet"
        record_id = "Alice#Bench#2"
        original_error = ValueError("Invalid input")
        custom_status = "CRASHED"

        with pytest.raises(RefVisionError) as exc_info:
            handle_error(
                meet_id=meet_id,
                record_id=record_id,
                error=original_error,
                status=custom_status,
            )

        mock_update.assert_called_once_with(
            meet_id,
            record_id,
            {
                "Status": "CRASHED",
                "ErrorMessage": "Invalid input",
            },
        )
        assert "RefVision Pipeline error => Invalid input" in str(exc_info.value)
