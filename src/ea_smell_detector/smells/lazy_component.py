import ea_smell_catalog_detector as core

def detect(graph, results=None):
    return [core.evidence(graph, [node], "name contains controller or manager")
            for node in graph if any(term in core.lower(core.node_name(graph, node)) for term in ("controller", "manager"))]
