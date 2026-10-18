import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found = []
    for data in graph:
        if core.node_type(graph, data) != "dataobject":
            continue
        components = core.related_of_type(graph, data, {"applicationcomponent"}, {"accessrelationship"})
        if len(components) > 1:
            for component in components:
                if len(core.related_of_type(graph, component, {"dataobject"}, {"accessrelationship"})) == 1:
                    found.append(core.evidence(graph, [data, component], "component shares exactly one data object"))
    return found
