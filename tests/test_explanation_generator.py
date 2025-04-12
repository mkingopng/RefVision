# tests/test_explanation_generator.py
"""
test bedrock explanation generator
"""
# import json
# import pytest
# from unittest.mock import patch, mock_open, MagicMock
# from botocore.exceptions import ClientError
# from refvision.explanation.explanation_generator import (
#     load_prompt_template,
#     load_decision_json,
#     load_decision_json_from_dynamodb,
#     generate_explanation,
#     handler,
# )
#
#
# def test_load_prompt_template():
#     """
#     Mocks open(...) to test reading the prompt template file.
#     """
#     fake_content = "Prompt with {decision_json} placeholder."
#     with patch("builtins.open", mock_open(read_data=fake_content)):
#         result = load_prompt_template("some_fake_path.txt")
#     assert result == fake_content
#
#
# def test_load_decision_json():
#     """
#     Mocks open(...) to test reading a JSON file from disk.
#     """
#     fake_json = {"test": "value"}
#     with patch("builtins.open", mock_open(read_data=json.dumps(fake_json))):
#         data = load_decision_json("decision.json")
#     assert data == fake_json
#
#
# @pytest.fixture
# def mock_dynamodb():
#     """
#     A fixture to patch boto3.resource("dynamodb") usage in load_decision_json_from_dynamodb().
#     Yields a mock that you can configure in tests.
#     """
#     with patch(
#         "refvision.explanation.explanation_generator.boto3.resource"
#     ) as mock_resource:
#         yield mock_resource
#
#
# def test_load_decision_json_from_dynamodb_success(mock_dynamodb):
#     """
#     Ensures load_decision_json_from_dynamodb returns the 'decision_json' item if found.
#     """
#     # set-up the mock
#     mock_table = MagicMock()
#     mock_dynamodb.return_value.Table.return_value = mock_table
#
#     # we simulate a successful get_item returning an Item with 'decision_json'
#     mock_table.get_item.return_value = {"Item": {"decision_json": {"some": "data"}}}
#
#     result = load_decision_json_from_dynamodb("lifter123", "attempt2", "sortXYZ")
#     assert result == {"some": "data"}
#
#     # also confirm the key we used in get_item
#     mock_table.get_item.assert_called_once_with(
#         Key={"LifterID_LiftID": "lifter123_attempt2", "SortKey": "sortXYZ"}
#     )
#
#
# def test_load_decision_json_from_dynamodb_no_item(mock_dynamodb):
#     """
#     If no item is found, we expect a ValueError.
#     """
#     mock_table = MagicMock()
#     mock_dynamodb.return_value.Table.return_value = mock_table
#     mock_table.get_item.return_value = {"Item": None}
#
#     with pytest.raises(
#         ValueError,
#         match="No decision found for lifter123_attempt2 with sort key 'sortXYZ'",
#     ):
#         load_decision_json_from_dynamodb("lifter123", "attempt2", "sortXYZ")
#
#
# @pytest.fixture
# def mock_bedrock():
#     """
#     Patches the bedrock-runtime client creation & returns a mock client.
#     """
#     with patch(
#         "refvision.explanation.explanation_generator.boto3.client"
#     ) as mock_client_factory:
#         mock_client = MagicMock()
#         mock_client_factory.return_value = mock_client
#         yield mock_client
#
#
# def test_generate_explanation_success(mock_bedrock):
#     """
#     generate_explanation should parse the bedrock response & return the 'completion' text.
#     """
#     # setup bedrock mock
#     fake_body = MagicMock()
#     fake_body.read.return_value = json.dumps(
#         {"completion": "Here is an explanation."}
#     ).encode("utf-8")
#
#     mock_bedrock.invoke_model.return_value = {"body": fake_body}
#
#     test_decision = {"decision": "No Lift"}
#     test_prompt = "Prompt with {decision_json}"
#     result = generate_explanation(test_decision, test_prompt)
#
#     # check the final result
#     assert result == "Here is an explanation."
#
#     # confirm we invoked bedrock
#     mock_bedrock.invoke_model.assert_called_once()
#     # if you want to check specific payload data, you can parse it from call args:
#     args, kwargs = mock_bedrock.invoke_model.call_args
#     assert kwargs["modelId"] == "anthropic.claude-v2"
#     # etc.
#
#
# def test_generate_explanation_client_error(mock_bedrock):
#     """
#     If bedrock-runtime throws a ClientError, we raise a RuntimeError from generate_explanation.
#     """
#     mock_bedrock.invoke_model.side_effect = ClientError(
#         error_response={"Error": {"Message": "Some bedrock error"}},
#         operation_name="InvokeModel",
#     )
#     with pytest.raises(RuntimeError, match="Bedrock invocation error"):
#         generate_explanation({}, "some prompt")
#
#
# def test_handler_success(mock_dynamodb, mock_bedrock):
#     """
#     The handler should:
#       1) load the prompt template
#       2) load decision from DynamoDB
#       3) call bedrock & return the explanation
#     """
#     # patch open(...) for prompt template
#     with patch(
#         "refvision.explanation.explanation_generator.open",
#         mock_open(read_data="Prompt: {decision_json}"),
#     ):
#         # setup the DB mock to return an item
#         mock_table = MagicMock()
#         mock_dynamodb.return_value.Table.return_value = mock_table
#         mock_table.get_item.return_value = {"Item": {"decision_json": {"some": "data"}}}
#
#         # setup bedrock mock
#         fake_body = MagicMock()
#         fake_body.read.return_value = json.dumps(
#             {"completion": "Explained text."}
#         ).encode("utf-8")
#         mock_bedrock.invoke_model.return_value = {"body": fake_body}
#
#         event = {
#             "lifter_id": "lifter123",
#             "lift_attempt": "attempt2",
#             "sort_key": "sortXYZ",
#         }
#         result = handler(event, context=None)
#         # expect "statusCode": 200, "body": "Explained text."
#         assert result["statusCode"] == 200
#         assert result["body"] == "Explained text."
#
#
# def test_handler_missing_args():
#     """
#     If 'lifter_id' or 'lift_attempt' is missing, ValueError is raised.
#     """
#     from refvision.explanation.explanation_generator import handler
#
#     # event missing 'lifter_id'
#     with pytest.raises(ValueError, match="must be provided"):
#         handler({"lift_attempt": "attempt2"}, None)
#
#     # event missing 'lift_attempt'
#     with pytest.raises(ValueError, match="must be provided"):
#         handler({"lifter_id": "lifter123"}, None)
