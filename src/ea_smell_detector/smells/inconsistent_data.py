import ea_smell_catalog_detector as core

def detect(graph, results=None):
    flow, found = core.directed_simple(graph, core.FLOW_RELS), []
    and_junctions = [n for n in graph if core.node_type(graph, n) == "junction"
                     and core.lower(graph.nodes[n].get("properties", {}).get("type", "")) == "and"]
    for junction in and_junctions:
        for data in graph:
            if core.node_type(graph, data) in core.DATA_TYPES and core.nx.has_path(flow, junction, data):
                found.append(core.evidence(graph, [junction, data], "AND split reaches data object"))
    return found
