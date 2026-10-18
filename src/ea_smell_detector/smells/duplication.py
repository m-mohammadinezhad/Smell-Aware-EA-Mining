from difflib import SequenceMatcher
import ea_smell_catalog_detector as core

def detect(graph, results=None):
    nodes, found = list(graph), []
    if len(nodes) > 2000:
        return found
    for index, first in enumerate(nodes):
        for second in nodes[index + 1:]:
            first_name, second_name = core.node_name(graph, first), core.node_name(graph, second)
            first_clean, second_clean = core.lower(first_name).strip(), core.lower(second_name).strip()
            if not first_clean or not second_clean:
                continue
            # ArchiMate's default labels are type names, not evidence that two
            # elements implement the same architectural capability.
            if first_clean in core.GENERIC_ELEMENT_NAMES or second_clean in core.GENERIC_ELEMENT_NAMES:
                continue
            similarity = SequenceMatcher(None, first_clean, second_clean).ratio()
            if core.node_type(graph, first) == core.node_type(graph, second) and similarity >= 0.85:
                found.append(core.evidence(graph, [first, second], f"name similarity={similarity:.2f}"))
    return found
