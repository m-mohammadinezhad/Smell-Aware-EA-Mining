def is_service_type(elem_type: str) -> bool:
    t = (elem_type or "").lower()
    return any(s in t for s in ["businessservice", "applicationservice", "technologyservice"])

def detect_chatty_services(G, element_details, threshold=3):
    service_nodes = [n for n in G.nodes() if is_service_type(element_details.get(n, {}).get("type", ""))]
    chatty_nodes = []

    for node in service_nodes:
        interactions = 0
        neighbors = set(G.successors(node)).union(set(G.predecessors(node)))
        for nbr in neighbors:
            nbr_type = element_details.get(nbr, {}).get("type", "").lower()
            if "service" in nbr_type:
                interactions += 1
        if interactions > threshold:
            chatty_nodes.append(node)

    return chatty_nodes


def detect(graph, results=None):
    """Detect services directly connected to more than three peer services."""
    import ea_smell_catalog_detector as core

    found = []
    for node in graph:
        if core.node_type(graph, node) not in core.SERVICE_TYPES:
            continue
        peers = [other for other in core.neighbours(graph, node)
                 if core.node_type(graph, other) in core.SERVICE_TYPES]
        if len(peers) > 3:
            found.append(core.evidence(graph, [node, *peers], f"service interactions={len(peers)}"))
    return found
