import ea_smell_catalog_detector as core

def detect(graph, results=None):
    flow, found = core.directed_simple(graph, core.FLOW_RELS), []
    verbs = ("test", "verify", "execute", "evaluate")
    for node in graph:
        if not any(verb in core.lower(core.node_name(graph, node)) for verb in verbs):
            continue
        successors = list(flow.successors(node))
        or_junctions = [n for n in successors if core.node_type(graph, n) == "junction"
                        and core.lower(graph.nodes[n].get("properties", {}).get("type", "")) == "or"]
        if not or_junctions or any(flow.out_degree(junction) == 1 for junction in or_junctions):
            found.append(core.evidence(graph, [node, *or_junctions], "test-like element lacks a two-way outcome"))
    return found
