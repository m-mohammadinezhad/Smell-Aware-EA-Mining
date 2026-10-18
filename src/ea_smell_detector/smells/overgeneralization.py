import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found = []
    for component in graph:
        if core.node_type(graph, component) != "applicationcomponent":
            continue
        interfaces = core.related_of_type(graph, component, core.INTERFACE_TYPES, {"compositionrelationship"})
        services = core.related_of_type(graph, component, {"applicationservice"}, {"realizationrelationship"})
        functions = core.related_of_type(graph, component, {graph.nodes[x]["type"] for x in graph},
                                         {"associationrelationship", "assignmentrelationship"})
        if len(interfaces) == 1 and len(services) == 1 and len(functions) > 3:
            found.append(core.evidence(graph, [component, *interfaces, *services, *functions],
                                       "many functions behind one interface/service"))
    return found
