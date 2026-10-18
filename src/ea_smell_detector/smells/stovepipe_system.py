from difflib import SequenceMatcher
import ea_smell_catalog_detector as core

def detect(graph, results=None):
    found, nodes = [], list(graph)
    if len(nodes) > 2000:
        return found
    for index, first in enumerate(nodes):
        for second in nodes[index + 1:]:
            first_interfaces = core.related_of_type(graph, first, core.INTERFACE_TYPES)
            second_interfaces = core.related_of_type(graph, second, core.INTERFACE_TYPES)
            similarity = SequenceMatcher(
                None, core.lower(core.node_name(graph, first)), core.lower(core.node_name(graph, second))
            ).ratio()
            if first_interfaces and second_interfaces and similarity >= 0.6:
                found.append(core.evidence(graph, [first, second, *first_interfaces, *second_interfaces],
                                           f"name similarity={similarity:.2f}"))
    return found
