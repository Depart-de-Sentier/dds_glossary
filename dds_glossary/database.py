"""Database classes for the dds_glossary package."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, joinedload, with_polymorphic
from sqlalchemy_utils import create_database, database_exists, drop_database

from .model import Base, Collection, Concept, ConceptScheme, Member, SemanticRelation
from .settings import get_settings


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
    database_url = database_url or get_settings().DATABASE_URL.get_secret_value()
    engine = create_engine(database_url)

    if database_exists(engine.url):
        if not drop_database_flag:
            return engine
        drop_database(engine.url)
        engine.dispose()

    create_database(engine.url)
    Base.metadata.create_all(engine)
    return engine


def save_dataset(
    engine: Engine,
    concept_schemes: list[ConceptScheme],
    concepts: list[Concept],
    collections: list[Collection],
    semantic_relations: list[SemanticRelation],
) -> None:
    """
    Save a dataset in the database.

    Args:
        engine (Engine): The database engine.
        concept_schemes (list[ConceptScheme]): The concept schemes.
        concepts (list[Concept]): The concepts.
        collections (list[Collection]): The collections.
        semantic_relations (list[SemanticRelation]): The semantic relations.
    """
    with Session(engine) as session:
        session.add_all(concept_schemes)
        session.add_all(concepts)
        session.add_all(collections)
        session.add_all(semantic_relations)

        members: list[Member] = []
        members.extend(concepts)
        members.extend(collections)
        for collection in collections:
            collection.resolve_members_from_xml(members)
        session.commit()


def get_concept_schemes(engine: Engine) -> list[ConceptScheme]:
    """
    Get the concept schemes from the database.

    Args:
        engine (Engine): The database engine.

    Returns:
        list[ConceptScheme]: The concept schemes.
    """
    with Session(engine) as session:
        return session.query(ConceptScheme).all()


def get_concept_scheme(engine: Engine, concept_scheme_iri: str) -> ConceptScheme:
    """
    Get the concept scheme from the database.

    Args:
        engine (Engine): The database engine.
        concept_scheme_iri (str): The concept scheme IRI.

    Returns:
        ConceptScheme: The concept scheme.

    Raises:
        NoResultFound: If the concept scheme is not found.
    """
    with Session(engine) as session:
        member_polymorphic = with_polymorphic(
            Member,
            [Concept, Collection],
            aliased=True,
        )
        return (
            session.query(ConceptScheme)
            .where(ConceptScheme.iri == concept_scheme_iri)
            .options(joinedload(ConceptScheme.members.of_type(member_polymorphic)))
            .one()
        )


def get_collection(engine: Engine, collection_iri: str) -> Collection:
    """
    Get the collection from the database.

    Args:
        engine (Engine): The database engine.
        collection_iri (str): The collection IRI.

    Returns:
        Collection: The collection.

    Raises:
        NoResultFound: If the collection is not found.
    """
    with Session(engine) as session:
        member_polymorphic = with_polymorphic(
            Member,
            [Concept, Collection],
            aliased=True,
        )
        return (
            session.query(Collection)
            .where(Collection.iri == collection_iri)
            .options(joinedload(Collection.members.of_type(member_polymorphic)))
            .one()
        )


def get_concept(engine: Engine, concept_iri: str) -> Concept:
    """
    Get the concept from the database.

    Args:
        engine (Engine): The database engine.
        concept_iri (str): The concept IRI.

    Return:
        Concept: The concept or None if not found.

    Raises:
        NoResultFound: If the concept is not found.
    """
    with Session(engine) as session:
        return (
            session.query(Concept)
            .where(Concept.iri == concept_iri)
            .options(joinedload(Concept.concept_schemes))
            .one()
        )


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


def search_database(
    engine: Engine,
    search_term: str,
    lang: str = "en",
) -> list[Concept]:
    """
    Search the database for concepts with the search_term in the preferred or
    alternative labels, in the specified language.

    Args:
        engine (Engine): The database engine.
        search_term (str): The search term to match against.
        lang (str, optional): The language of the labels. Defaults to "en".

    Returns:
        list[Concept]: The concepts that matches the search term.
    """
    with Session(engine) as session:
        concepts = session.query(Concept).all()
        return [
            concept
            for concept in concepts
            if search_term in concept.get_in_language(concept.prefLabels, lang)
            or search_term in concept.get_in_language(concept.altLabels, lang)
        ]
