import logging
from typing import Any, Dict, List, Tuple

from . import services

import neo4j
from owlready2 import get_ontology

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


def load_services_dataset(driver: neo4j.Driver, dataset: services.Dataset, dataset_path: str, import_chunk_size: int=1000):
    """
    Load a given dataset into a Neo4J instance
    """
    ontology = get_ontology(dataset.url).load()
    ontology.save(file=str(dataset_path), format="rdfxml")
    concept_schemes_raw, concepts_raw, _, semantic_relations_raw = services.GlossaryController.parse_dataset(dataset_path)

    logging.info("Loaded the dataset in memory")

    concept_schemes = [c.to_dict() for c in concept_schemes_raw]
    concepts = [c.to_dict() for c in concepts_raw]
    semantic_relations = [c.to_dict() for c in semantic_relations_raw]

    # One service.Dataset has exactly one concept scheme
    main_concept_scheme = concept_schemes[0]

    logging.info("Importing concept schemes...")

    # Load concept schemes
    for chunk in chunk_list(concept_schemes, import_chunk_size):
        query, args = build_nodes_import_query_and_args(["ConceptScheme"], chunk)
        driver.execute_query(query, args)

    logging.info("Imported concept schemes")

    logging.info("Importing concepts...")

    # Load concepts
    for chunk in chunk_list(concepts, import_chunk_size):
        query, args = build_nodes_import_query_and_args(["Concept"], chunk)
        driver.execute_query(query, args)
    
    logging.info("Imported concept schemes")

    logging.info("Adding indices...")

    # Index by the IRI
    for key, label in [("ConceptScheme", "iri"), ("Concept", "iri")]:
        driver.execute_query(build_index_query(key=key, label=label))

    logging.info("Added indices...")

    logging.info("Importing concept -> concept scheme relationships...")

    # Load concept -> concept scheme relationships
    for concept in concepts:
        edge_type = "inScheme"
        edge =  ("Concept", concept["iri"], "ConceptScheme", main_concept_scheme["iri"])
        query, args = build_edges_import_query_and_args([edge_type], [edge])
        driver.execute_query(query, args)

    logging.info("Imported concept -> concept scheme relationships")

    logging.info("Importing concept -> concept 'broader' relationships...")

    # Load concept "broader" their relationships
    for semantic_relation in semantic_relations:
        edge_type = semantic_relations[0]["type"]

        edge =  ("Concept", semantic_relation["source_concept_iri"], "Concept", semantic_relation["target_concept_iri"])
        
        query, args = build_edges_import_query_and_args([edge_type], [edge])
        driver.execute_query(query, args)

    logging.info("Imported concept -> concept 'broader' relationships")


def build_nodes_import_query_and_args(labels: List[str], nodes: List[Dict[str, Any]]):
    """
    Bulk import nodes into Neo4J

    ## Example

    > build_nodes_import_query_and_args(["Hello", "World"], [{"a": 1, "b": 2}, {"a": 1, "c": 10}])
    (
        "MERGE (e_0:Hello:World) {a: $a_0, b: $b_0}\nMERGE (e_1:Hello:World) {a: $a_1, c: $c_1}",
        {'a_0': 1, 'b_0': 2, 'a_1': 1, 'c_1': 10}
    )
    """
    query_args = {}
    for idx, node in enumerate(nodes):
        for k, v in node.items():
            query_args[f"{k}_{idx}"] = v

    schema_keys = set()
    for node in nodes:
        for k in node.keys():
            schema_keys.add(k)

    node_labels_str = ':'.join(labels)
    
    query_rows = []
    for idx, node in enumerate(nodes):
        schema_kv = [f"{k}: ${k}_{idx}" for k in node.keys()]
        query_row = f"MERGE (e_{idx}:{node_labels_str} {{{', '.join(schema_kv)}}})"
        query_rows.append(query_row)

    query = "\n".join(query_rows)
    return query, query_args


def build_edges_import_query_and_args(labels: List[str], edges: List[Tuple[str, str, str, str]]):
    """
    Bulk import nodes into Neo4J

    ## Example

    > build_edges_import_query_and_args(["IsFrom"], [("Concept", "def", "ConceptScheme", "abcd")])
    (
        "MATCH (src_0:Concept {iri: $iri_src_0}), (tgt_0: ConceptScheme {iri: $iri_tgt_0})\nWITH src_0, tgt_0\nMERGE (src_0)-[r_0:IsFrom]->(tgt_0)",
        {'iri_src_0': 'def', 'iri_tgt_0': 'abcd'}
    )
    """
    query_args = {}
    for idx, edge in enumerate(edges):
        _, source_iri, _, target_iri = edge 
        query_args[f"iri_src_{idx}"] = source_iri
        query_args[f"iri_tgt_{idx}"] = target_iri
    
    edge_labels_str = ":".join(labels)

    matches = []
    withs = []
    merges = []
    for idx, edge in enumerate(edges):
        source_label, source_iri, target_label, target_iri = edge 
        matches.extend([
            f"(src_{idx}:{source_label} {{iri: $iri_src_{idx}}})",
            f"(tgt_{idx}:{target_label} {{iri: $iri_tgt_{idx}}})"
        ])
        withs.extend([f"src_{idx}", f"tgt_{idx}"])
        merges.extend([f"(src_{idx})-[r_{idx}:{edge_labels_str}]->(tgt_{idx})"])

    query = f"""
    MATCH {', '.join(matches)}
    """
    for merge in merges:
        query += f"MERGE {merge}"

    return query, query_args


def build_index_query(label: str, key: str):
    """
    Build indices for a list of keys on labels
    """
    return f"CREATE INDEX {label}_{key}_index IF NOT EXISTS FOR (c:{label}) ON (c.{key})"


def chunk_list(lst: list, n: int):
    """
    Yield successive n-sized chunks from list `lst`.
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
