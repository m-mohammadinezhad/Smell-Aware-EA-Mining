import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found = []
    structural = {"assignmentrelationship", "compositionrelationship", "associationrelationship",
                  "aggregationrelationship", "realizationrelationship"}
    for node in graph:
        if core.node_type(graph, node) not in core.SERVICE_TYPES:
            continue
        data = core.related_of_type(graph, node, core.DATA_TYPES, {"accessrelationship"})
        non_service = [other for other in core.neighbours(graph, node)
                       if core.node_type(graph, other) not in core.SERVICE_TYPES
                       and core.has_relation(graph, node, other, structural)]
        if data and not non_service:
            found.append(core.evidence(graph, [node, *data], "service only exposes data access"))
    return found
