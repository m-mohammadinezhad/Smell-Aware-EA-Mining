import ea_smell_catalog_detector as core

def detect(graph, results=None):
    flow, found = core.directed_simple(graph, core.FLOW_RELS), []
    processes = [n for n in graph if core.node_type(graph, n) in core.PROCESS_TYPES]
    for delete_process in processes:
        if "delete" not in core.lower(core.node_name(graph, delete_process)):
            continue
        for read_process in processes:
            if "read" in core.lower(core.node_name(graph, read_process)) and core.nx.has_path(flow, delete_process, read_process):
                found.append(core.evidence(graph, [delete_process, read_process], "delete process reaches read process"))
    return found
