import ea_smell_catalog_detector as core

def detect(graph, results=None):
    flow, found = core.directed_simple(graph, core.FLOW_RELS), []
    junctions = [n for n in graph if core.node_type(graph, n) == "junction"]
    junction_type = lambda n: core.lower(graph.nodes[n].get("properties", {}).get("type", ""))
    for start in junctions:
        for end in junctions:
            if junction_type(start) == "and" and junction_type(end) == "or" and flow.in_degree(end) > 1 and core.nx.has_path(flow, start, end):
                found.append(core.evidence(graph, [start, end], "AND split reaches OR merge"))
    return found
