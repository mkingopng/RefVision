# tests/test_log_forwarder.py
"""

"""
# import base64
# import gzip
# import json
# import time
# from typing import Any, Dict
#
# import pytest
# from refvision.log_forwarder import log_forwarder
#
# # A sample dummy payload resembling a CloudWatch Logs event.
# # You can adjust the structure as needed.
# DUMMY_PAYLOAD = {
#     "messageType": "DATA_MESSAGE",
#     "owner": "123456789012",
#     "logGroup": "/aws/lambda/VideoIngestionFunction",
#     "logStream": "dummy-stream",
#     "subscriptionFilters": ["dummy-filter"],
#     "logEvents": [
#         {
#             "stack_id": "1",
#             "timestamp": int(time.time() * 1000),
#             "message": "Test log event 1",
#         },
#         {
#             "stack_id": "2",
#             "timestamp": int(time.time() * 1000),
#             "message": "Test log event 2",
#         },
#     ],
# }
#
#
# def encode_payload(payload: Dict[str, Any]) -> str:
#     """
#     Compress and encode the payload in the same way CloudWatch Logs does.
#     """
#     json_data = json.dumps(payload).encode("utf-8")
#     compressed = gzip.compress(json_data)
#     encoded = base64.b64encode(compressed).decode("utf-8")
#     return encoded
#
#
# @pytest.fixture
# def sample_event() -> Dict[str, Any]:
#     """
#     Returns a simulated CloudWatch Logs event.
#     """
#     return {"awslogs": {"data": encode_payload(DUMMY_PAYLOAD)}}
#
#
# class DummyLogsClient:
#     """A dummy logs client to capture calls to put_log_events."""
#
#     def __init__(self):
#         self.put_log_events_called = False
#         self.last_put_params = None
#
#     def create_log_stream(self, logGroupName: str, logStreamName: str) -> None:
#         # Simulate successful creation.
#         pass
#
#     def describe_log_streams(
#         self, logGroupName: str, logStreamNamePrefix: str
#     ) -> Dict[str, Any]:
#         # Return a dummy stream without a sequence token.
#         return {"logStreams": [{"logStreamName": logStreamNamePrefix}]}
#
#     def put_log_events(self, **kwargs) -> Dict[str, Any]:
#         self.put_log_events_called = True
#         self.last_put_params = kwargs
#         # Simulate a successful call returning a new sequence token.
#         return {"nextSequenceToken": "dummy-token"}
#
#
# @pytest.fixture
# def dummy_logs_client(monkeypatch) -> DummyLogsClient:
#     dummy = DummyLogsClient()
#     # Patch the logs_client in log_forwarder module.
#     monkeypatch.setattr(log_forwarder, "logs_client", dummy)
#     return dummy
#
#
# def test_log_forwarder_handler(
#     sample_event: Dict[str, Any], dummy_logs_client: DummyLogsClient
# ):
#     """
#     Test the log_forwarder Lambda handler by simulating an incoming CloudWatch Logs event.
#     """
#     # Call the handler.
#     response = log_forwarder.handler(sample_event, None)
#
#     # Check that the handler returned a success response.
#     assert response["statusCode"] == 200
#     assert "Log events forwarded successfully" in response["body"]
#
#     # Verify that our dummy put_log_events method was called.
#     assert (
#         dummy_logs_client.put_log_events_called
#     ), "Expected put_log_events to be called"
#
#     # Check that the required keys are in the parameters.
#     params = dummy_logs_client.last_put_params
#     assert "logGroupName" in params
#     assert "logStreamName" in params
#     assert "logEvents" in params
#     assert len(params["logEvents"]) == len(DUMMY_PAYLOAD["logEvents"])
