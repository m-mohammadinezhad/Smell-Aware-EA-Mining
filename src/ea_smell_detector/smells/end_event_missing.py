import ea_smell_catalog_detector as core

def detect(graph, results=None):
    flow = core.directed_simple(graph, core.FLOW_RELS)
    if not any(core.node_type(graph, node) in core.EVENT_TYPES for node in graph):
        return []
    return [core.evidence(graph, [node], "process has no outgoing flow relation")
            for node in graph if core.node_type(graph, node) in core.PROCESS_TYPES and flow.out_degree(node) == 0]
