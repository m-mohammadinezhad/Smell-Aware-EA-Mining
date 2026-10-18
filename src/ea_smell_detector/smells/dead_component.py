import ea_smell_catalog_detector as core

def detect(graph, results=None):
    graph_undirected = core.undirected(graph)
    return [core.evidence(graph, [node], "no incoming or outgoing relationships")
            for node in graph if graph_undirected.degree(node) == 0]
