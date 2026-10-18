import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found = []
    behavior_types = {"applicationfunction", "applicationprocess", "applicationservice"}
    for behavior in graph:
        if core.node_type(graph, behavior) not in behavior_types:
            continue
        components = core.related_of_type(graph, behavior, {"applicationcomponent"}, {"realizationrelationship"})
        if len(components) > 1:
            found.append(core.evidence(graph, [behavior, *components],
                                       "one application behavior realized by multiple components"))
    return found
