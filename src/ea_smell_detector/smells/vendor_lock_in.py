import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found, markers = [], ("external", "vendor", "ibm", "microsoft", "amazon", "provision")
    for node in graph:
        props = graph.nodes[node].get("properties", {})
        marked = any(marker in core.lower(core.node_name(graph, node)) for marker in ("external", "vendor"))
        marked = marked or any(marker in core.lower(key) or marker in core.lower(value)
                               for key, value in props.items() for marker in markers[2:])
        if marked and not core.related_of_type(graph, node, core.INTERFACE_TYPES):
            found.append(core.evidence(graph, [node], "external/vendor designation without interface"))
    return found
