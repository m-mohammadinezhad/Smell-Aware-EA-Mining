import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found = []
    relation_types = {"assignmentrelationship", "realizationrelationship"}
    for node in graph:
        # Match the catalogue's directed Cypher query:
        # (m)-[:AssignmentRelationship|RealizationRelationship]->(n).
        behaviors = [
            target for _, target, data in graph.out_edges(node, data=True)
            if core.relation_type(data) in relation_types
        ]
        if len(behaviors) > 1:
            found.append(core.evidence(graph, [node, *behaviors], f"behaviors={len(behaviors)}"))
    return found
