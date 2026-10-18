import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found, structural = [], {"assignmentrelationship", "compositionrelationship",
                             "associationrelationship", "aggregationrelationship", "realizationrelationship"}
    for service in graph:
        if core.node_type(graph, service) not in core.SERVICE_TYPES:
            continue
        data = core.related_of_type(graph, service, core.DATA_TYPES, {"accessrelationship"})
        served_by = [n for n in core.neighbours(graph, service)
                     if core.has_relation(graph, n, service, {"servingrelationship", "associationrelationship"})]
        own_structure = core.related_of_type(graph, service, {graph.nodes[n]["type"] for n in graph}, structural)
        if data and served_by and not [n for n in own_structure if core.node_type(graph, n) not in core.SERVICE_TYPES]:
            found.append(core.evidence(graph, [service, *data, *served_by], "service delegates to data service"))
    return found
