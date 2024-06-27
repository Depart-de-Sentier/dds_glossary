"""Authentication utils for the dds_glossary package."""

from http import HTTPStatus

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from pydantic import ValidationError

from .settings import get_settings

api_key_header = APIKeyHeader(name="X-API-Key")


def get_api_key(api_key: str = Depends(api_key_header)) -> dict[str, str]:
    """Get the API key from the header 'X-API-Key'.

    Args:
        api_key (str): The API key. Defaults to Depends(api_key_header),
            which is the header 'X-API-Key'.

    Returns:
        dict[str, str]: The API key.

    Raises:
        HTTPException: If the API key is missing or invalid. Or if the API key
            environment variable is missing.
    """
    error = HTTPException(
        status_code=HTTPStatus.FORBIDDEN,
        detail="Invalid API Key",
    )
    try:
        correct_api_key = get_settings().API_KEY.get_secret_value()
        if api_key != correct_api_key:
            raise error
    except ValidationError as ve:
        raise error from ve
    return {"api_key": api_key}
