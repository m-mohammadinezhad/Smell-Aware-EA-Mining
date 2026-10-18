import ea_smell_catalog_detector as core

def detect(graph, results=None):
    return [core.evidence(graph, [node], "documentation length > 256")
            for node in graph if len(graph.nodes[node].get("documentation", "")) > 256]
