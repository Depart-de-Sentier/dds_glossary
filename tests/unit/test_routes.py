"""Tests for dds_glossary.routes module."""

from http import HTTPStatus

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from dds_glossary.model import Dataset, FailedDataset
from dds_glossary.schema import InitDatasetsResponse, VersionResponse
from dds_glossary.settings import get_settings


def test_version(
    client: TestClient,
    version_response: VersionResponse,
) -> None:
    """Test the /version endpoint."""
    response = client.get("/latest/version")
    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/json"
    assert response.json() == version_response.model_dump()


def test_init_datasets_missing_key(client: TestClient) -> None:
    """Test the /init_datasets endpoint with a missing API key."""
    response = client.post("/latest/init_datasets")
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"detail": "Not authenticated"}


def test_init_datasets_invalid_key(client: TestClient) -> None:
    """Test the /init_datasets endpoint with an invalid API key."""
    response = client.post("/latest/init_datasets", headers={"X-API-Key": "invalid"})
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.headers["content-type"] == "application/json"
    assert response.json() == {"detail": "Invalid API Key"}


def test_init_datasets_valid_key(client: TestClient, monkeypatch: MonkeyPatch) -> None:
    """Test the /init_datasets endpoint."""
    saved_datasets = [Dataset(name="saved.rdf", url="http://example.com/saved.rdf")]
    failed_datasets = [
        FailedDataset(
            name="failed.rdf",
            url="http://example.com/failed.rdf",
            error="error",
        )
    ]
    monkeypatch.setattr(
        "dds_glossary.services.GlossaryController.init_datasets",
        lambda *_, **__: InitDatasetsResponse(
            saved_datasets=saved_datasets,
            failed_datasets=failed_datasets,
        ),
    )

    api_key = get_settings().API_KEY.get_secret_value()
    response = client.post("/latest/init_datasets", headers={"X-API-Key": api_key})
    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/json"
    assert (
        response.json()
        == InitDatasetsResponse(
            saved_datasets=saved_datasets, failed_datasets=failed_datasets
        ).model_dump()
    )


def test_get_concept_schemes_empty(client: TestClient) -> None:
    """Test the /schemes endpoint with an empty database."""
    response = client.get("/latest/schemes")
    assert response.json() == []
    assert response.status_code == HTTPStatus.OK
    assert response.headers["content-type"] == "application/json"


def test_get_concept_scheme_not_found(client: TestClient) -> None:
    """Test the /scheme endpoint."""
    concept_scheme_iri = "iri"
    response = client.get(f"/latest/scheme?concept_scheme_iri={concept_scheme_iri}")
    assert response.json() == {
        "detail": f"Concept scheme {concept_scheme_iri} not found."
    }
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["content-type"] == "application/json"


def test_get_collections_not_found(client: TestClient) -> None:
    """Test the /collections endpoint."""
    concept_scheme_iri = "iri"
    response = client.get(
        f"/latest/collections?concept_scheme_iri={concept_scheme_iri}"
    )
    assert response.json() == {
        "detail": f"Concept scheme {concept_scheme_iri} not found."
    }
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["content-type"] == "application/json"


def test_get_collection_not_found(client: TestClient) -> None:
    """Test the /collection endpoint."""
    collection_iri = "iri"
    response = client.get(f"/latest/collection?collection_iri={collection_iri}")
    assert response.json() == {"detail": f"Collection {collection_iri} not found."}
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["content-type"] == "application/json"


def test_get_concepts_not_found(client: TestClient) -> None:
    """Test the /concepts endpoint."""
    concept_scheme_iri = "iri"
    response = client.get(f"/latest/concepts?concept_scheme_iri={concept_scheme_iri}")
    assert response.json() == {
        "detail": f"Concept scheme {concept_scheme_iri} not found."
    }
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["content-type"] == "application/json"


def test_get_concept_not_found(client: TestClient) -> None:
    """Test the /concept endpoint."""
    concept_iri = "iri"
    response = client.get(f"/latest/concept?concept_iri={concept_iri}")
    assert response.json() == {"detail": f"Concept {concept_iri} not found."}
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["content-type"] == "application/json"
