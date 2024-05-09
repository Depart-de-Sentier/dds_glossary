"""Database classes for the dds_glossary package."""

from os import getenv

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database, database_exists

from .model import Base, Concept, ConceptScheme, SemanticRelation


def init_engine(
    database_url: str | None = None,
    drop_database_flag: bool = False,
) -> Engine:
    """
    Initialize the database engine. If the database does not exist, create it.
    If the drop_database_flag is set, drop the database if it exists. Create the
    tables if they do not exist.

    Args:
        database_url (str, optional): The database URL. If None, use the
            `DATABASE_URL` environment variable.
        drop_database_flag (bool): Flag to drop the database if it exists.

    Returns:
        Engine: The database engine.

    Raises:
        ValueError: If the DATABASE_URL environment variable is not set, in case the
            the `database_url` argument is None.
    """
    if database_url is None:
        database_url = getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set.")

    engine = create_engine(database_url)
    if not database_exists(engine.url):
        create_database(engine.url)
    elif drop_database_flag:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    return engine


def save_dataset(
    engine: Engine,
    concept_schemes: list[ConceptScheme],
    concepts: list[Concept],
    semantic_relations: list[SemanticRelation],
) -> None:
    """
    Save a dataset in the database.

    Args:
        engine (Engine): The database engine.
        concept_schemes (list[ConceptScheme]): The concept schemes.
        concepts (list[Concept]): The concepts.
        semantic_relations (list[SemanticRelation]): The semantic relations.
    """
    with Session(engine) as session:
        session.add_all(concept_schemes)
        session.add_all(concepts)
        session.add_all(semantic_relations)
        session.commit()


def get_concept_schemes(engine: Engine) -> list[ConceptScheme]:
    """
    Get the concept schemes from the database.

    Returns:
        list[ConceptScheme]: The concept schemes.
    """
    with Session(engine) as session:
        return session.query(ConceptScheme).all()


def get_concepts(engine: Engine, concept_scheme_iri: str) -> list[Concept]:
    """
    Get the concepts from the database.

    Args:
        engine (Engine): The database engine.
        concept_scheme_iri (str): The concept scheme IRI.

    Returns:
        list[Concept]: The concepts.
    """
    with Session(engine) as session:
        return (
            session.query(Concept).where(Concept.scheme_iri == concept_scheme_iri).all()
        )


def get_concept(engine: Engine, concept_iri: str) -> Concept | None:
    """
    Get the concept from the database, if found.

    Args:
        engine (Engine): The database engine.
        concept_iri (str): The concept IRI.

    Return:
        Concept | None: The concept or None if not found.
    """
    with Session(engine) as session:
        return session.query(Concept).where(Concept.iri == concept_iri).one_or_none()


def get_relations(engine: Engine, concept_iri: str) -> list[SemanticRelation]:
    """
    Get the relations from the database.

    Args:
        engine (Engine): The database engine.
        concept_iri (str): The concept IRI.

    Returns:
        list[SemanticRelation]: The relations.
    """
    with Session(engine) as session:
        return (
            session.query(SemanticRelation)
            .where(
                (SemanticRelation.source_concept_iri == concept_iri)
                | (SemanticRelation.target_concept_iri == concept_iri)
            )
            .all()
        )
