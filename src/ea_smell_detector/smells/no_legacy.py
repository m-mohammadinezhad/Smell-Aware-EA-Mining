import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found = []
    for node in graph:
        props = graph.nodes[node].get("properties", {})
        marked = "legacy" in core.lower(core.node_name(graph, node)) or any(
            "legacy" in core.lower(value) for value in props.values()
        )
        related = [n for n in core.neighbours(graph, node) if core.node_type(graph, n) in {"workpackage", "plateau"}]
        if marked and related:
            found.append(core.evidence(graph, [node, *related], "legacy element linked to migration element"))
    return found
