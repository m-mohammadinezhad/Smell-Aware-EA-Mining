import ea_smell_catalog_detector as core

def detect(graph, results=None):
    flow = core.directed_simple(graph, core.FLOW_RELS)
    junctions = [n for n in graph if core.node_type(graph, n) == "junction"]
    junction_type = lambda n: core.lower(graph.nodes[n].get("properties", {}).get("type", ""))
    return [core.evidence(graph, [start, end], "OR junction reaches AND junction")
            for start in junctions if junction_type(start) == "or"
            for end in junctions if junction_type(end) == "and" and core.nx.has_path(flow, start, end)]
