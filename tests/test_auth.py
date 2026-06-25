import pytest
from fastapi import HTTPException
import config
from auth import verify_api_key


def test_valid_key_passes(monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "my-secret")
    result = verify_api_key("my-secret")
    assert result == "my-secret"


def test_invalid_key_raises_401(monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "my-secret")
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key("wrong-key")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "unauthorized"


def test_empty_key_raises_401(monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "my-secret")
    with pytest.raises(HTTPException) as exc_info:
        verify_api_key("")
    assert exc_info.value.status_code == 401
