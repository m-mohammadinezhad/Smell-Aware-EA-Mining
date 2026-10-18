from collections import Counter
import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found, graph_undirected = [], core.undirected(graph)
    for community in core.nx.connected_components(graph_undirected):
        types = Counter(core.node_type(graph, node) for node in community)
        relationships = graph_undirected.subgraph(community).number_of_edges()
        aggregations = sum(1 for left, right, data in graph.edges(data=True)
                           if left in community and right in community
                           and core.relation_type(data) in {"compositionrelationship", "aggregationrelationship"})
        if any(count > 3 for count in types.values()) and relationships > 10 and (
            aggregations == 0 or relationships / aggregations > 3
        ):
            found.append(core.evidence(graph, community, "dense unaggregated community"))
    return found
