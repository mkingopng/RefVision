# tests/test_inference_trigger.py
"""
test inference trigger
"""
import json
from unittest.mock import patch
from refvision.inference.inference_trigger import handler


def test_handler_with_arn():
    """
    If STATE_MACHINE_ARN is set, the function should call sf_client.start_execution
    with the event data, and return HTTP 200.
    """
    event = {"foo": "bar"}

    # patch the module-level STATE_MACHINE_ARN and sf_client
    with patch(
        "refvision.inference.inference_trigger.STATE_MACHINE_ARN", "mockARN"
    ), patch("refvision.inference.inference_trigger.sf_client") as mock_sf_client:
        # mock return from start_execution
        mock_sf_client.start_execution.return_value = {
            "executionArn": "mockExecutionARN"
        }

        result = handler(event, context=None)

        assert result["statusCode"] == 200
        assert "Inference trigger processed." in result["body"]

        # ensure start_execution was called with the correct ARN and input
        mock_sf_client.start_execution.assert_called_once_with(
            stateMachineArn="mockARN", input=json.dumps(event)
        )


def test_handler_no_arn():
    """
    If STATE_MACHINE_ARN is empty, the function should skip calling start_execution
    and simply return HTTP 200.
    """
    event = {"hello": "world"}

    # patch the module-level STATE_MACHINE_ARN to an empty string
    with patch("refvision.inference.inference_trigger.STATE_MACHINE_ARN", ""), patch(
        "refvision.inference.inference_trigger.sf_client"
    ) as mock_sf_client:
        result = handler(event, context=None)

        assert result["statusCode"] == 200
        assert "Inference trigger processed." in result["body"]

        # ensure start_execution was NOT called
        mock_sf_client.start_execution.assert_not_called()


def test_handler_start_execution_exception(caplog):
    """
    If there's an exception during start_execution, it should log the error
    and still return 200 with a 'processed' message.
    """
    event = {"test": "data"}

    with patch(
        "refvision.inference.inference_trigger.STATE_MACHINE_ARN", "mockARN"
    ), patch("refvision.inference.inference_trigger.sf_client") as mock_sf_client:
        mock_sf_client.start_execution.side_effect = Exception("Some error")

        result = handler(event, context=None)
        assert result["statusCode"] == 200
        assert "Inference trigger processed." in result["body"]

        # we should see the error message in the logs
        assert "Error starting state machine execution: Some error" in caplog.text
        mock_sf_client.start_execution.assert_called_once()
