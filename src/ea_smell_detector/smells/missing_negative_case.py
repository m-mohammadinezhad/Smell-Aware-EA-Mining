import ea_smell_catalog_detector as core

def detect(graph, results=None):
    flow, found = core.directed_simple(graph, core.FLOW_RELS), []
    positives = ("successfully", "without errors", "in time", "develop")
    for node in graph:
        if not any(word in core.lower(core.node_name(graph, node)) for word in positives):
            continue
        predecessors = list(flow.predecessors(node))
        has_or = any(core.node_type(graph, p) == "junction"
                     and core.lower(graph.nodes[p].get("properties", {}).get("type", "")) == "or"
                     for p in predecessors)
        if not has_or:
            found.append(core.evidence(graph, [node], "positive outcome without OR alternative"))
    return found
