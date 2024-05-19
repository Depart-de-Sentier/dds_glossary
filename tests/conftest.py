"""Fixtures for dds_glossary tests."""

from pathlib import Path
from typing import Generator

from defusedxml.lxml import parse as parse_xml
from fastapi.testclient import TestClient
from owlready2 import onto_path
from pytest import fixture
from sqlalchemy.engine import Engine
from sqlalchemy_utils import database_exists, drop_database

from dds_glossary.controllers import GlossaryController
from dds_glossary.database import init_engine
from dds_glossary.main import create_app
from dds_glossary.model import Collection, Concept, ConceptScheme, SemanticRelation


@fixture(name="dir_data")
def _dir_data() -> Path:
    return Path(__file__).parent / "data"


@fixture(name="file_rdf")
def _file_rdf(dir_data: Path) -> Path:
    return dir_data / "sample.rdf"


@fixture(name="root_element")
def _root_element(file_rdf: Path):
    tree = parse_xml(file_rdf)
    return tree.getroot()


@fixture(name="concept_scheme")
def _concept_scheme(
    root_element,  # pylint: disable=redefined-outer-name
) -> ConceptScheme:
    return ConceptScheme.from_xml_element(
        root_element.find("core:ConceptScheme", namespaces=root_element.nsmap)
    )


@fixture(name="collection")
def _collection(
    root_element,  # pylint: disable=redefined-outer-name
    concept_scheme: ConceptScheme,  # pylint: disable=redefined-outer-name
) -> Collection:
    return Collection.from_xml_element(
        root_element.find("core:Collection", namespaces=root_element.nsmap),
        [concept_scheme],
    )


@fixture(name="concept")
def _concept(
    root_element,  # pylint: disable=redefined-outer-name
    concept_scheme: ConceptScheme,  # pylint: disable=redefined-outer-name
) -> Concept:
    return Concept.from_xml_element(
        root_element.find("core:Concept", namespaces=root_element.nsmap),
        [concept_scheme],
    )


@fixture(name="semantic_relation")
def _semantic_relation(
    root_element,  # pylint: disable=redefined-outer-name
) -> SemanticRelation:
    return SemanticRelation.from_xml_element(
        root_element.find("core:Concept", namespaces=root_element.nsmap)
    )[0]


def _clean_database(_engine: Engine) -> None:
    if database_exists(_engine.url):
        drop_database(_engine.url)


@fixture(name="engine")
def _engine() -> Generator[Engine, None, None]:
    engine = init_engine(drop_database_flag=True)
    yield engine
    _clean_database(engine)


@fixture(name="controller")
def _controller(tmp_path: Path) -> Generator[GlossaryController, None, None]:
    controller = GlossaryController(data_dir_path=tmp_path)
    yield controller
    _clean_database(controller.engine)


@fixture(name="client")
def _client(tmp_path: Path) -> Generator[TestClient, None, None]:
    app = create_app()
    app.state.controller.data_dir = tmp_path
    app.state.controller.engine = init_engine(drop_database_flag=True)
    onto_path.append(str(tmp_path))
    with TestClient(app) as client:
        yield client
    _clean_database(app.state.controller.engine)
