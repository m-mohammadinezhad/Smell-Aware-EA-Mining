import ea_smell_catalog_detector as core

def detect(graph, results=None):
    sensitive = {"confident", "sensible", "classified", "sensitive"}
    found = []
    for node in graph:
        props = graph.nodes[node].get("properties", {})
        marked = any(word in core.lower(key) or word in core.lower(value)
                     for key, value in props.items() for word in sensitive)
        accessors = core.related_of_type(
            graph, node, {graph.nodes[x]["type"] for x in graph}, {"accessrelationship"}
        )
        if core.node_type(graph, node) in core.DATA_TYPES and marked and len(accessors) > 2:
            found.append(core.evidence(graph, [node, *accessors], f"access count={len(accessors)}"))
    return found
