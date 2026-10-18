import networkx as nx


def compute_s1_modularity(H: nx.Graph, modularity_threshold: float = 0.30):
    """
    S1: Weak / Low Modularity
    S1 = 1 - Q
    where Q is Louvain modularity.
    """

    S1 = 0.0
    Q = 0.0
    num_communities = 0

    # Small or sparse partial views do not contain enough information for a
    # modularity judgement.  This prevents a simple process chain from being
    # labelled as a weakened-modularity smell.
    if H.number_of_nodes() >= 5 and H.number_of_edges() >= 4:
        communities = list(nx.algorithms.community.greedy_modularity_communities(H))
        Q = nx.algorithms.community.modularity(H, communities)
        S1 = 1.0 - Q
        num_communities = len(communities)

    return {
        "S1": S1,
        "Q_modularity": Q,
        "num_communities": num_communities,
        "modularity_threshold": modularity_threshold,
        "is_weakened_modularity": num_communities > 0 and Q < modularity_threshold,
    }


def detect(graph, results=None):
    """Detect models whose global modularity is below the configured threshold."""
    import ea_smell_catalog_detector as core

    result = compute_s1_modularity(core.undirected(graph))
    if not result["is_weakened_modularity"]:
        return []
    return [core.evidence(
        graph, graph.nodes,
        f"Q={result['Q_modularity']:.4f} < {result['modularity_threshold']:.2f}",
    )]
