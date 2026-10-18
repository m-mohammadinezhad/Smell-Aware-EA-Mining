import networkx as nx


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def compute_s2_dense_structure(H: nx.Graph):
    """
    S2: Dense Structure
    Ratio of nodes whose clustering coefficient is
    above the 90th percentile.
    """

    S2 = 0.0
    num_dense_nodes = 0
    threshold_dense = 0.0

    # At least three nodes are needed for a closed triangular structure.
    # A three-node chain has coefficients of zero, whereas a three-node
    # triangle has coefficients of one and is therefore a valid dense case.
    if H.number_of_nodes() > 2:

        clustering = nx.clustering(H)
        values = list(clustering.values())

        if len(values) > 1:

            threshold_dense = _percentile(values, 0.90)

            dense_nodes = [
                n for n, c in clustering.items()
                if c > 0.0 and c >= threshold_dense
            ]

            num_dense_nodes = len(dense_nodes)

            S2 = num_dense_nodes / H.number_of_nodes()

    return {
        "S2": S2,
        "num_dense_nodes": num_dense_nodes,
        "dense_threshold": threshold_dense,
        "dense_nodes": dense_nodes if H.number_of_nodes() > 2 else [],
        "clustering": clustering if H.number_of_nodes() > 2 else {},
    }


def detect(graph, results=None):
    """Detect elements in the dense structural core of a model."""
    import ea_smell_catalog_detector as core

    result = compute_s2_dense_structure(core.undirected(graph))
    if not result["dense_nodes"]:
        return []
    return [core.evidence(
        graph, result["dense_nodes"],
        f"clustering coefficient >= P90 ({result['dense_threshold']:.4f})",
    )]
