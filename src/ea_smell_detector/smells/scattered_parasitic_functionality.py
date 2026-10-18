import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found = []
    for concern in graph:
        if core.node_type(graph, concern) not in {"applicationfunction", "applicationservice", "goal"}:
            continue
        targets = [n for n in core.neighbours(graph, concern)
                   if core.node_type(graph, n) in {"applicationcomponent", "assessment"}]
        if len(targets) > 1:
            found.append(core.evidence(graph, [concern, *targets], f"concern affects {len(targets)} targets"))
    return found
