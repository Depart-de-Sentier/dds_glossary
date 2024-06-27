"""Integration test for a fresh start scenario."""

from http import HTTPStatus
from pathlib import Path
from typing import Mapping

from fastapi.testclient import TestClient

from dds_glossary.model import Collection, Concept, ConceptScheme
from dds_glossary.schema import VersionResponse
from dds_glossary.settings import get_settings

from .utils import (
    Endpoint,
    RequestType,
    assert_response,
    not_found_response,
    setup_fresh_start,
)


def test_api_cycle(
    client: TestClient,
    dir_data: Path,
    concept_scheme: ConceptScheme,
    concept: Concept,
    collection: Collection,
    version_response: VersionResponse,
) -> None:
    """Test the API cycle from a fresh start."""
    api_key = get_settings().API_KEY.get_secret_value()
    lang = "sk"
    invalid_iri = "non_existing"
    responses = setup_fresh_start(
        dir_data,
        concept_scheme,
        concept,
        lang=lang,
    )

    # /version endpoint
    assert_response(
        _client=client,
        endpoint=Endpoint.VERSION.value,
        https_status=HTTPStatus.OK,
        response_model=version_response,
    )

    # /init_datasets endpoint
    headers: Mapping[str, str] = {"X-API-Key": api_key}
    assert_response(
        _client=client,
        endpoint=Endpoint.INIT_DATASETS.value,
        https_status=HTTPStatus.OK,
        response_model=responses[Endpoint.INIT_DATASETS],
        request_type=RequestType.POST,
        headers=headers,
    )

    # /schemes endpoint
    assert_response(
        _client=client,
        endpoint=f"{Endpoint.SCHEMES.value}?lang={lang}",
        https_status=HTTPStatus.OK,
        response_model=responses[Endpoint.SCHEMES],
    )

    # /scheme endpoint scheme found
    assert_response(
        _client=client,
        endpoint=(
            f"{Endpoint.SCHEME.value}?concept_scheme_iri="
            f"{concept_scheme.iri}&lang={lang}"
        ),
        https_status=HTTPStatus.OK,
        response_model=responses[Endpoint.SCHEME],
    )

    # /scheme endpoint scheme not found
    assert_response(
        _client=client,
        endpoint=(
            f"{Endpoint.SCHEME.value}?concept_scheme_iri=" f"{invalid_iri}&lang={lang}"
        ),
        https_status=HTTPStatus.NOT_FOUND,
        response_model=not_found_response(
            entity_name="Concept scheme",
            entity_iri=invalid_iri,
        ),
    )

    # /collections endpoint scheme found
    assert_response(
        _client=client,
        endpoint=(
            f"{Endpoint.COLLECIONS.value}?concept_scheme_iri="
            f"{concept_scheme.iri}&lang={lang}"
        ),
        https_status=HTTPStatus.OK,
        response_model=responses[Endpoint.COLLECIONS],
    )

    # /collections endpoint scheme not found
    assert_response(
        _client=client,
        endpoint=(
            f"{Endpoint.COLLECIONS.value}?concept_scheme_iri="
            f"{invalid_iri}&lang={lang}"
        ),
        https_status=HTTPStatus.NOT_FOUND,
        response_model=not_found_response(
            entity_name="Concept scheme",
            entity_iri=invalid_iri,
        ),
    )

    # /collection endpoint collection found
    assert_response(
        _client=client,
        endpoint=(
            f"{Endpoint.COLLECION.value}?collection_iri="
            f"{collection.iri}&lang={lang}"
        ),
        https_status=HTTPStatus.OK,
        response_model=responses[Endpoint.COLLECION],
    )

    # /collection endpoint collection not found
    assert_response(
        _client=client,
        endpoint=(
            f"{Endpoint.COLLECION.value}?collection_iri=" f"{invalid_iri}&lang={lang}"
        ),
        https_status=HTTPStatus.NOT_FOUND,
        response_model=not_found_response(
            entity_name="Collection",
            entity_iri=invalid_iri,
        ),
    )

    # /concepts endpoint scheme found
    assert_response(
        _client=client,
        endpoint=(
            f"{Endpoint.CONCEPTS.value}?concept_scheme_iri="
            f"{concept_scheme.iri}&lang={lang}"
        ),
        https_status=HTTPStatus.OK,
        response_model=responses[Endpoint.CONCEPTS],
    )

    # /concepts endpoint scheme not found
    assert_response(
        _client=client,
        endpoint=(
            f"{Endpoint.CONCEPTS.value}?concept_scheme_iri="
            f"{invalid_iri}&lang={lang}"
        ),
        https_status=HTTPStatus.NOT_FOUND,
        response_model=not_found_response(
            entity_name="Concept scheme",
            entity_iri=invalid_iri,
        ),
    )

    # /concept endpoint concept found
    assert_response(
        _client=client,
        endpoint=(
            f"{Endpoint.CONCEPT.value}?concept_iri=" f"{concept.iri}&lang={lang}"
        ),
        https_status=HTTPStatus.OK,
        response_model=responses[Endpoint.CONCEPT],
    )

    # /concept endpoint concept not found
    assert_response(
        _client=client,
        endpoint=(
            f"{Endpoint.CONCEPT.value}?concept_iri=" f"{invalid_iri}&lang={lang}"
        ),
        https_status=HTTPStatus.NOT_FOUND,
        response_model=not_found_response(
            entity_name="Concept",
            entity_iri=invalid_iri,
        ),
    )
