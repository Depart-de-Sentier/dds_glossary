"""Tests for dds_glossary.auth module."""

from http import HTTPStatus

from fastapi import HTTPException
from pytest import ExceptionInfo, MonkeyPatch
from pytest import raises as pytest_raises

from dds_glossary.auth import get_api_key
from dds_glossary.settings import get_settings


def _validate_error(exc_info: ExceptionInfo) -> None:
    assert exc_info.value.status_code == HTTPStatus.FORBIDDEN
    assert exc_info.value.detail == "Invalid API Key"


def test_get_api_key_missing_env_var(monkeypatch: MonkeyPatch) -> None:
    """Test the get_api_key function with a missing API_KEY environment variable."""
    monkeypatch.delenv("API_KEY", raising=False)
    with pytest_raises(HTTPException) as exc_info:
        get_api_key()
    _validate_error(exc_info)


def test_get_api_key_missing_header() -> None:
    """Test the get_api_key function with a missing header."""
    with pytest_raises(HTTPException) as exc_info:
        get_api_key(api_key="")
    _validate_error(exc_info)


def test_get_api_key_invalid_key() -> None:
    """Test the get_api_key function with an invalid key."""
    with pytest_raises(HTTPException) as exc_info:
        get_api_key(api_key="invalid")
    _validate_error(exc_info)


def test_get_api_key_valid_key() -> None:
    """Test the get_api_key function with a valid key."""
    api_key = get_settings().API_KEY.get_secret_value()
    assert get_api_key(api_key=api_key) == {"api_key": api_key}
