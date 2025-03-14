# tests/test_model_loader.py
"""
Tests for the model_loader module functions.
"""
import pytest
import torch
from pathlib import Path
from refvision.inference import model_loader
from typing import Any
import types


def dummy_yolo(model_path: str) -> Any:
    """
    fake YOLO class for testing purposes
    :param model_path:
    :return:
    """
    model = types.SimpleNamespace()
    model.model_path = model_path  # ✅ Add this to match real YOLO behavior
    model.model = torch.nn.Module()  # Mimic a PyTorch model structure
    model.overrides = {"verbose": True}
    model.fuse = lambda: model  # Mock `fuse()` to do nothing
    model.to = lambda *args, **kwargs: model  # Mock `.to(device)`
    return model


def test_load_model_file_not_found(tmp_path: Path) -> None:
    """
    Test that load_model raises FileNotFoundError when the model file does not
    exist
    :param tmp_path: (Path) A temporary directory provided by pytest.
    :return: None
    """
    non_existent_file = tmp_path / "nonexistent.pt"
    with pytest.raises(FileNotFoundError):
        model_loader.load_model(str(non_existent_file))


def test_load_model_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Test that load_model successfully returns a model and device when given a
    valid file. This test writes a dummy file and then patches the YOLO class
    in model_loader to use the dummy_yolo implementation.
    :param tmp_path: A temporary directory provided by pytest.
    :param monkeypatch: The pytest monkeypatch fixture.
    :return: None
    """
    dummy_file = tmp_path / "dummy_model.pt"
    dummy_file.write_text("dummy content")
    monkeypatch.setattr(model_loader, "YOLO", dummy_yolo)  # Mock YOLO
    model, device = model_loader.load_model(str(dummy_file))
    assert hasattr(model, "model_path")  # ✅ Now this check is valid
    assert model.model_path == str(dummy_file)
    assert isinstance(device, torch.device)  # ✅ Checks the device type
    assert device.type in ["cuda", "cpu"]  # ✅ Ensures it runs on GPU or CPU
    assert model is not None  # ✅ Model should be initialized properly
