import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found = []
    dependency_types = {"servingrelationship", "associationrelationship", "influencerelationship", "accessrelationship"}
    for node in graph:
        dependencies = [n for n in graph.successors(node) if core.has_relation(graph, node, n, dependency_types)]
        if len(dependencies) > 3:
            found.append(core.evidence(graph, [node, *dependencies], f"dependent abstractions={len(dependencies)}"))
    return found
