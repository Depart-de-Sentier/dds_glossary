"""Tests for dds_glossary.database module."""

from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from dds_glossary.database import (
    get_collection,
    get_concept,
    get_concept_scheme,
    get_concept_schemes,
    get_relations,
    init_engine,
    save_dataset,
    search_database,
)
from dds_glossary.enums import SemanticRelationType
from dds_glossary.model import Collection, Concept, ConceptScheme, SemanticRelation

from ..common import add_collections, add_concept_schemes, add_concepts, add_relations


def engine_init_checks(engine: Engine) -> None:
    """Check the engine initialization.

    Args:
        engine (Engine): The database engine.

    Returns:
        None
    """
    assert engine is not None

    inspector = inspect(engine)
    assert inspector.has_table("concept_schemes")
    assert inspector.has_table("collections")
    assert inspector.has_table("concepts")
    assert inspector.has_table("semantic_relations")
    assert inspector.has_table("in_scheme")
    assert inspector.has_table("in_collection")


def test_init_engine_database_not_exists_no_drop() -> None:
    """Test the init_engine function when the database does not exist and
    drop_database_flag is False."""
    engine = init_engine(drop_database_flag=False)
    engine_init_checks(engine)


def test_init_engine_database_not_exists_drop() -> None:
    """Test the init_engine function when the database does not exist and
    drop_database_flag is True."""
    engine = init_engine(drop_database_flag=True)
    engine_init_checks(engine)


def test_init_engine_database_exists_no_drop() -> None:
    """Test the init_engine function when the database exists and
    drop_database_flag is False."""
    engine = init_engine(drop_database_flag=False)
    engine = init_engine(drop_database_flag=False)
    engine_init_checks(engine)


def test_init_engine_database_exists_drop() -> None:
    """Test the init_engine function when the database exists and
    drop_database_flag is True."""
    engine = init_engine(drop_database_flag=False)
    engine = init_engine(drop_database_flag=True)
    engine_init_checks(engine)


def test_save_dataset_with_no_data(engine: Engine) -> None:
    """Test the save_dataset function with empty data."""
    save_dataset(engine, [], [], [], [])
    with Session(engine) as session:
        assert session.query(ConceptScheme).count() == 0
        assert session.query(Concept).count() == 0
        assert session.query(Collection).count() == 0
        assert session.query(SemanticRelation).count() == 0


def test_save_dataset_with_data(engine: Engine) -> None:
    """Test the save_dataset function with data."""
    concept_scheme_iri = "http://example.org/concept_scheme"
    concept1_iri = "http://example.org/concept1"
    concept2_iri = "http://example.org/concept2"
    concept_schemes = [
        ConceptScheme(
            iri=concept_scheme_iri,
            notation="Concept Scheme Notation",
            scopeNote="Concept Scheme Scope Note",
            prefLabels=[{"en": "Concept Scheme Pref Label"}],
        )
    ]
    concepts = [
        Concept(
            iri=concept1_iri,
            identifier="Concept1 Identifier",
            notation="Concept Notation",
            prefLabels=[{"en": "Concept1 Pref Label"}],
            altLabels=[{"en": "Concept1 Alt Label"}],
            scopeNotes=["Concept1 Scope Note"],
        ),
        Concept(
            iri=concept2_iri,
            identifier="Concept2 Identifier",
            notation="Concept2 Notation",
            prefLabels=[{"en": "Concept2 Pref Label"}],
            altLabels=[{"en": "Concept2 Alt Label"}],
            scopeNotes=["Concept2 Scope Note"],
        ),
    ]
    collections = [
        Collection(
            iri="collection_iri0",
            notation="Collection Notation",
            prefLabels=[{"en": "Collection Pref Label 0"}],
            member_iris=[concept1_iri, concept2_iri],
        ),
    ]
    semantic_relations = [
        SemanticRelation(
            type=SemanticRelationType.BROADER,
            source_concept_iri=concepts[0].iri,
            target_concept_iri=concepts[1].iri,
        )
    ]

    save_dataset(engine, concept_schemes, concepts, collections, semantic_relations)

    with Session(engine) as session:
        assert session.query(ConceptScheme).count() == 1
        assert session.query(Concept).count() == 2
        assert session.query(SemanticRelation).count() == 1
        assert session.query(ConceptScheme).one().iri == concept_scheme_iri
        assert session.query(Concept).all()[0].iri == concept1_iri
        assert session.query(SemanticRelation).one().source_concept_iri == concept1_iri
        assert session.query(SemanticRelation).one().target_concept_iri == concept2_iri


def test_get_concept_schemes(engine: Engine) -> None:
    """Test the get_concept_schemes."""
    concept_scheme_dicts = add_concept_schemes(engine, 1)

    concept_schemes = get_concept_schemes(engine)
    assert len(concept_schemes) == len(concept_scheme_dicts)
    assert concept_schemes[0].to_dict() == concept_scheme_dicts[0]


def test_get_concept_scheme(engine: Engine) -> None:
    """Test the get_concept_scheme."""
    concept_scheme_dicts = add_concept_schemes(engine, 1)
    _ = add_concepts(engine, [concept_scheme_dicts[0]["iri"]] * 3)

    concept_scheme = get_concept_scheme(engine, concept_scheme_dicts[0]["iri"])
    assert concept_scheme is not None
    assert concept_scheme.to_dict() == concept_scheme_dicts[0]


def test_get_collection(engine: Engine) -> None:
    """Test the get_collection."""
    concept_scheme_dicts = add_concept_schemes(engine, 1)
    concept_dicts = add_concepts(engine, [concept_scheme_dicts[0]["iri"]] * 3)
    member_iri_lists = [
        [
            concept_dicts[0]["iri"],
            concept_dicts[1]["iri"],
        ]
    ]
    collection_dicts = add_collections(
        engine,
        [concept_scheme_dicts[0]["iri"]],
        member_iri_lists,
    )

    collection = get_collection(engine, collection_dicts[0]["iri"])
    assert collection is not None
    assert collection.to_dict() == collection_dicts[0]
    assert len(collection.members) == len(member_iri_lists[0])
    assert collection.members[0].to_dict() == concept_dicts[0]
    assert collection.members[1].to_dict() == concept_dicts[1]


def test_get_concept(engine: Engine) -> None:
    """Test the get_concept."""
    concept_scheme_dicts = add_concept_schemes(engine, 1)
    concept_dicts = add_concepts(engine, [concept_scheme_dicts[0]["iri"]])

    concept = get_concept(engine, concept_dicts[0]["iri"])
    assert concept is not None
    assert concept.to_dict() == concept_dicts[0]


def test_get_relations(engine: Engine) -> None:
    """Test the get_relations."""
    concept_scheme_dicts = add_concept_schemes(engine, 1)
    scheme_iri = concept_scheme_dicts[0]["iri"]
    concept_dicts = add_concepts(engine, [scheme_iri, scheme_iri])
    relation_dicts = add_relations(
        engine, [(concept_dicts[0]["iri"], concept_dicts[1]["iri"])]
    )

    relations = get_relations(engine, concept_dicts[0]["iri"])
    assert len(relations) == len(relation_dicts)
    assert relations[0].to_dict() == relation_dicts[0]


def test_search_database(engine: Engine) -> None:
    """Test the search_database."""
    concept_scheme_dicts = add_concept_schemes(engine, 1)
    scheme_iri = concept_scheme_dicts[0]["iri"]
    concept_dicts = add_concepts(engine, [scheme_iri, scheme_iri])

    search_results = search_database(engine, concept_dicts[0]["prefLabel"])
    assert len(search_results) == 1
    assert search_results[0].to_dict() == concept_dicts[0]


def test_search_database_no_results(engine: Engine) -> None:
    """Test the search_database when no results are found."""
    concept_scheme_dicts = add_concept_schemes(engine, 1)
    scheme_iri = concept_scheme_dicts[0]["iri"]
    add_concepts(engine, [scheme_iri, scheme_iri])

    search_results = search_database(engine, "prefLabel2")
    assert len(search_results) == 0
