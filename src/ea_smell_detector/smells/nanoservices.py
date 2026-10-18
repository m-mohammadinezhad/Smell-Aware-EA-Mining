import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found = []
    for node in graph:
        components = core.related_of_type(graph, node, {graph.nodes[x]["type"] for x in graph},
                                          {"compositionrelationship"})
        if len(components) >= 3:
            found.append(core.evidence(graph, [node, *components], f"composition count={len(components)}"))
    return found
