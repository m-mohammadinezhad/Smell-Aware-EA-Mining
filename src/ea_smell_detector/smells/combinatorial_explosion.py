import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found = []
    for target in graph:
        realizers = core.related_of_type(
            graph, target, {graph.nodes[n]["type"] for n in graph}, {"realizationrelationship"}
        )
        if len(realizers) > 1 and any(
            core.related_of_type(graph, r, core.DATA_TYPES, {"accessrelationship", "associationrelationship"})
            for r in realizers
        ):
            found.append(core.evidence(graph, [target, *realizers], "multiple realizers with data access"))
    return found
