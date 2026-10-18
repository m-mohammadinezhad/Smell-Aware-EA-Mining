import ea_smell_catalog_detector as core

def detect(graph, results=None):
    return [core.evidence(graph, [node], "junction has a non-junction name")
            for node in graph if core.node_type(graph, node) == "junction"
            and core.node_name(graph, node) and "junction" not in core.lower(core.node_name(graph, node))]
