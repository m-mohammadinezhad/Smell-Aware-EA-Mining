import ea_smell_catalog_detector as core

def detect(graph, results=None):
    pairs = {"min":"max", "open":"close", "start":"stop", "create":"destroy", "get":"set",
             "read":"write", "print":"scan", "first":"last", "begin":"end", "lock":"unlock",
             "show":"hide", "up":"down", "source":"target", "insert":"delete", "push":"pull",
             "enable":"disable", "acquire":"release", "left":"right", "on":"off"}
    names, found = [core.lower(core.node_name(graph, node)) for node in graph], []
    for node in graph:
        name = core.lower(core.node_name(graph, node))
        for first, second in pairs.items():
            if name.startswith(first) and not any(second in candidate for candidate in names):
                found.append(core.evidence(graph, [node], f"missing complementary term '{second}'"))
    return found
