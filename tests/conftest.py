# tests/conftest.py
"""
This file is used to define fixtures that can be used in multiple test files.
"""
import os
from dotenv import load_dotenv

# Load the .env file early so that all modules (including dynamodb_helpers)
# see the correct environment variables.
load_dotenv()

# Explicitly set/override the variables for local testing.
os.environ["AWS_ENDPOINT_URL"] = "http://localhost:4566"
os.environ["AWS_DEFAULT_REGION"] = "ap-southeast-2"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
os.environ["DYNAMODB_TABLE"] = "RefVisionMeetTest"