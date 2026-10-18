import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found = []
    for node in graph:
        if core.node_type(graph, node) not in {"actor", "workpackage"}:
            continue
        for key, value in graph.nodes[node].get("properties", {}).items():
            if key in {"staff", "members", "personnel", "size"}:
                try:
                    if float(value) > 4:
                        found.append(core.evidence(graph, [node], f"{key}={value}"))
                except ValueError:
                    continue
    return found
