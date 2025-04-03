# tests/test_config.py
"""
test the configuration module
"""
import os
import pytest
from unittest.mock import patch
from refvision.common.config import get_config, CONFIG_YAML_PATH


@pytest.fixture
def clear_env(monkeypatch):
    """
    Clears or overrides environment variables to ensure a clean test environment.
    By default, unsets REFVISION_ENV, AWS_REGION, and so on, so we can test
    behaviour from scratch.
    """
    # Save old environment
    old_env = dict(os.environ)
    # Clear out or pop keys that might affect the test
    keys_to_remove = [
        "REFVISION_ENV",
        "FLASK_APP_MODE",
        "AWS_REGION",
        "VIDEO_NAME",
        "VIDEO_FILENAME",
        "S3_BUCKET",
        "S3_BUCKET_RAW",
        "DYNAMODB_TABLE",
        # add any others you want to forcibly remove
    ]
    for k in keys_to_remove:
        monkeypatch.delenv(k, raising=False)

    yield  # test runs here

    # Restore old environment
    for k, v in old_env.items():
        os.environ[k] = v
    # Also remove keys that weren't in old_env
    for k in set(os.environ) - set(old_env):
        del os.environ[k]


def test_default_local_mode(clear_env):
    """
    If REFVISION_ENV is not set, it defaults to 'local'.
    """
    # The fixture cleared out REFVISION_ENV
    cfg = get_config()
    assert cfg["ENV_MODE"] == "local"
    assert cfg["FLASK_APP_MODE"] == "Local"
    # Because it's local, we expect some local directories to be set
    assert "DATA_DIR" in cfg
    assert "TEMP_DIR" in cfg
    assert "OUTPUT_DIR" in cfg
    # Check some default region
    assert cfg["AWS_REGION"] == "ap-southeast-2"


@pytest.mark.parametrize("env_mode", ["local", "cloud"])
def test_env_modes(clear_env, env_mode, monkeypatch):
    """
    Check that get_config() sets expected keys for both local and cloud modes.
    """
    monkeypatch.setenv("REFVISION_ENV", env_mode)
    cfg = get_config()
    assert cfg["ENV_MODE"] == env_mode

    if env_mode == "local":
        # local-only keys or local settings we expect
        assert cfg["INGESTION_MODE"] == "simulated"
        assert "DATA_DIR" in cfg
        assert "TEMP_DIR" in cfg
        assert "MODEL_PATH" in cfg
    else:
        # cloud
        # e.g. we expect these keys to exist, but might differ from local
        assert "S3_BUCKET" in cfg
        # Possibly we expect config["AWS_ENDPOINT_URL"] to come from environment
        # or remain None
        # ...
        assert (
            cfg.get("DATA_DIR") is None
        ), "Should not define local directories in cloud mode."


def test_invalid_env_mode(clear_env, monkeypatch):
    """
    If REFVISION_ENV is set to an invalid string, get_config() should raise ValueError.
    """
    monkeypatch.setenv("REFVISION_ENV", "banana")
    with pytest.raises(ValueError, match="Unknown REFVISION_ENV=banana"):
        get_config()


def test_local_directories_created(clear_env, monkeypatch):
    """
    In local mode, get_config() attempts to create local directories (data_dir, temp_dir, output_dir).
    We'll patch 'os.makedirs' to ensure it's called with the right paths.
    """
    monkeypatch.setenv("REFVISION_ENV", "local")

    with patch("os.makedirs") as mock_makedirs:
        cfg = get_config()

    # We expect it to have called 'os.makedirs' for each directory
    # The calls may happen in any order, so check that each directory is in the calls
    calls = [call.args[0] for call in mock_makedirs.call_args_list]
    assert cfg["DATA_DIR"] in calls
    assert cfg["TEMP_DIR"] in calls
    assert cfg["OUTPUT_DIR"] in calls


def test_yaml_config_loaded():
    """
    Optionally, you can test if config.yaml exists and loads without error.
    This is somewhat redundant, but can confirm that the file is valid YAML.
    """
    assert os.path.exists(CONFIG_YAML_PATH), "config.yaml should exist"
    # If you want to parse it with the same method, just do get_config() here:
    cfg = get_config()
    # Check that something from config.yaml is present, e.g. "LIFTER_SELECTOR"
    # or "s3_bucket_raw", etc.
    # This depends on what your config.yaml has.
    assert "LIFTER_SELECTOR" in cfg
