import ea_smell_catalog_detector as core

def detect(graph, results=None):
    return [core.evidence(graph, [node], "name contains ' or '")
            for node in graph if core.node_type(graph, node) != "junction"
            and " or " in core.lower(core.node_name(graph, node))]
