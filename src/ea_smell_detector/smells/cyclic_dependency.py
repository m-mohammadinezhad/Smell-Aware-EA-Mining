from collections import defaultdict
import networkx as nx

def detect_cyclic_dependencies(G, element_details):
    cycles_info = defaultdict(list)
    for scc in nx.strongly_connected_components(G):
        if len(scc) <= 1 or len(scc) > 10:
            continue
        cycle = list(scc)
        cycle_with_names = [
            f"{element_details.get(node_id, {}).get('name', node_id)} ({node_id})"
            for node_id in cycle
        ]
        for node_id in cycle:
            cycles_info[node_id].append(cycle_with_names)
    return dict(cycles_info)


def detect(graph, results=None):
    """Detect strongly connected components of up to ten elements."""
    import ea_smell_catalog_detector as core
    import networkx as nx

    found = []
    for component in nx.strongly_connected_components(core.directed_simple(graph)):
        if 1 < len(component) <= 10:
            found.append(core.evidence(graph, component, f"SCC size={len(component)}"))
    return found
