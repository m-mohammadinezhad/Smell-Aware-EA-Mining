import ea_smell_catalog_detector as core

def detect(graph, results=None):
    return [core.evidence(graph, [node], "name contains ' and '")
            for node in graph if " and " in core.lower(core.node_name(graph, node))]
