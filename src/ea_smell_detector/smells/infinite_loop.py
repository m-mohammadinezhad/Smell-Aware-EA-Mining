import ea_smell_catalog_detector as core

def detect(graph, results=None):
    graph_undirected, found = core.undirected(graph), []
    for component in core.nx.strongly_connected_components(core.directed_simple(graph)):
        external = any((left in component) ^ (right in component) for left, right in graph_undirected.edges())
        if 1 < len(component) <= 5 and not external:
            found.append(core.evidence(graph, component, "closed cyclic subgraph"))
    return found
