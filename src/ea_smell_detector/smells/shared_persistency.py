import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found = []
    all_types = {graph.nodes[node]["type"] for node in graph}
    for data in graph:
        data_type, name = core.node_type(graph, data), core.lower(core.node_name(graph, data))
        accessors = core.related_of_type(graph, data, all_types, {"accessrelationship"})
        db_like = data_type == "systemsoftware" and any(term in name for term in ("dbms", "data"))
        if len(accessors) > 1 and (data_type in core.DATA_TYPES or db_like):
            found.append(core.evidence(graph, [data, *accessors], f"accessors={len(accessors)}"))
    return found
