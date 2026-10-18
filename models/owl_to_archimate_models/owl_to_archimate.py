"""Create a concise ArchiMate model from the API-Gateway OWL knowledge graph.

The input ontology contains both architectural facts and individual API-call
events.  This converter keeps the architectural facts and aggregates the
event-level facts into relationships carrying a ``frequency`` property.

The output uses Archi's native .archimate XML format and can be opened
directly in Archi.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path


RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
ARCHI = "http://www.archimatetool.com/archimate"
XMI = "http://www.omg.org/XMI"

ET.register_namespace("xmi", XMI)
ET.register_namespace("xsi", XSI)
ET.register_namespace("archimate", ARCHI)


def local(value: str) -> str:
    """Return the local term from an RDF resource or XML tag."""
    return value.rsplit("#", 1)[-1].rsplit("/", 1)[-1].rsplit("}", 1)[-1]


def safe_id(prefix: str, text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:14]
    return f"{prefix}_{digest}"


def xml_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "unnamed"


def add_property(element: ET.Element, key: str, value: object) -> None:
    # Archi's native format keeps property elements directly below the model
    # element or relationship; a <properties> wrapper is not recognised.
    ET.SubElement(element, "property", key=key, value=str(value))


def node_name(node: ET.Element) -> str:
    labels = [
        child.text.strip()
        for child in node
        if child.tag == f"{{{RDFS}}}label" and child.text and child.text.strip()
    ]
    return labels[-1] if labels else node.attrib.get(f"{{{RDF}}}about", "unnamed")


def node_value(node: ET.Element, property_name: str) -> str | None:
    for child in node:
        if local(child.tag) == property_name and child.text:
            return child.text.strip()
    return None


def node_resources(node: ET.Element, property_name: str) -> list[str]:
    return [
        child.attrib[f"{{{RDF}}}resource"]
        for child in node
        if local(child.tag) == property_name
        and f"{{{RDF}}}resource" in child.attrib
    ]


def first_type(node: ET.Element) -> str | None:
    for child in node:
        if child.tag == f"{{{RDF}}}type":
            return child.attrib.get(f"{{{RDF}}}resource")
    return None


def parse_owl(path: Path) -> list[ET.Element]:
    root = ET.parse(path).getroot()
    return [
        node
        for node in root
        if local(node.tag) == "NamedIndividual"
        and node.attrib.get(f"{{{RDF}}}about")
    ]


def add_element(folder: ET.Element, element_type: str, name: str, key: str) -> str:
    element_id = safe_id("el", key)
    ET.SubElement(
        folder,
        "element",
        {f"{{{XSI}}}type": f"archimate:{element_type}", "name": name, "id": element_id},
    )
    return element_id


def add_relationship(
    folder: ET.Element,
    relationship_type: str,
    source: str,
    target: str,
    key: str,
    name: str = "",
    properties: dict[str, object] | None = None,
) -> str | None:
    if source == target:
        return None
    relation_id = safe_id("rel", key)
    relation = ET.SubElement(
        folder,
        "element",
        {
            f"{{{XSI}}}type": f"archimate:{relationship_type}",
            "name": name,
            "id": relation_id,
            "source": source,
            "target": target,
        },
    )
    for property_name, value in (properties or {}).items():
        add_property(relation, property_name, value)
    return relation_id


def add_view(
    folder: ET.Element,
    name: str,
    element_ids: list[str],
    relationships: list[ET.Element],
    x_offset: int = 80,
) -> None:
    """Create a simple grid view, including relationships between displayed nodes."""
    view = ET.SubElement(
        folder,
        "element",
        {
            f"{{{XSI}}}type": "archimate:ArchimateDiagramModel",
            "name": name,
            "id": safe_id("view", name),
        },
    )
    object_ids: dict[str, str] = {}
    objects: dict[str, ET.Element] = {}
    for index, element_id in enumerate(element_ids):
        object_id = safe_id("obj", f"{name}:{element_id}")
        object_ids[element_id] = object_id
        child = ET.SubElement(
            view,
            "child",
            {
                f"{{{XSI}}}type": "archimate:DiagramObject",
                "id": object_id,
                "archimateElement": element_id,
            },
        )
        objects[element_id] = child
        ET.SubElement(
            child,
            "bounds",
            x=str(x_offset + (index % 5) * 205),
            y=str(80 + (index // 5) * 115),
            width="175",
            height="55",
        )

    for relationship in relationships:
        source = relationship.attrib.get("source")
        target = relationship.attrib.get("target")
        relationship_id = relationship.attrib.get("id")
        if not source or not target or not relationship_id:
            continue
        if source not in object_ids or target not in object_ids:
            continue
        connection_id = safe_id("con", f"{name}:{relationship_id}")
        ET.SubElement(
            objects[source],
            "sourceConnection",
            {
                f"{{{XSI}}}type": "archimate:Connection",
                "id": connection_id,
                "source": object_ids[source],
                "target": object_ids[target],
                "archimateRelationship": relationship_id,
            },
        )
        previous = objects[target].attrib.get("targetConnections", "")
        objects[target].set(
            "targetConnections",
            " ".join(part for part in (previous, connection_id) if part),
        )


def build_model(nodes: list[ET.Element]) -> ET.Element:
    by_type: dict[str, list[ET.Element]] = defaultdict(list)
    by_about: dict[str, ET.Element] = {}
    for node in nodes:
        about = node.attrib[f"{{{RDF}}}about"]
        by_about[about] = node
        node_type = first_type(node)
        if node_type:
            by_type[node_type].append(node)

    model = ET.Element(
        "archimate:model",
        {
            f"{{{XMI}}}version": "2.0",
            "xmlns:archimate": ARCHI,
            "name": "API Gateway architecture mined from OWL",
            "id": "api_gateway_mined",
        },
    )
    business = ET.SubElement(model, "folder", name="Business", id="business", type="business")
    application = ET.SubElement(model, "folder", name="Application", id="application", type="application")
    other = ET.SubElement(model, "folder", name="Other", id="other", type="other")
    relations = ET.SubElement(model, "folder", name="Relations", id="relations", type="relations")
    views = ET.SubElement(model, "folder", name="Views", id="views", type="diagrams")

    elements: dict[str, str] = {}
    gateway_id = add_element(application, "ApplicationComponent", "API Gateway", "gateway")
    elements["gateway"] = gateway_id

    # Consumer applications and service destinations are architectural actors
    # at the application layer, not individual call events.
    consumer_ids: list[str] = []
    for node in by_type["core#ConsumerApp"]:
        about = node.attrib[f"{{{RDF}}}about"]
        name = node_value(node, "app_name") or node_name(node)
        element_id = add_element(application, "ApplicationComponent", name, f"consumer:{about}")
        elements[about] = element_id
        consumer_ids.append(element_id)
        add_relationship(
            relations, "FlowRelationship", element_id, gateway_id, f"consumer-gateway:{about}", "invokes"
        )

    destination_ids: list[str] = []
    for node in by_type["core#ServiceDestination"]:
        about = node.attrib[f"{{{RDF}}}about"]
        name = node_value(node, "endpoint_route") or node_name(node)
        element_id = add_element(application, "ApplicationComponent", name, f"destination:{about}")
        elements[about] = element_id
        destination_ids.append(element_id)

    # Operations are stable API behavior; resources/calls are event-level
    # instantiations and are therefore not created as hundreds of elements.
    operation_by_uri: dict[str, str] = {}
    operation_ids: list[str] = []
    operation_methods: dict[str, str] = {}
    for node in by_type["core#APIOperation"]:
        about = node.attrib[f"{{{RDF}}}about"]
        route = node_value(node, "endpoint_route") or node_name(node)
        method = node_value(node, "method") or route.split("_", 1)[0]
        name = route if route.startswith(method) else f"{method} {route}"
        element_id = add_element(application, "ApplicationService", name, f"operation:{about}")
        elements[about] = element_id
        operation_ids.append(element_id)
        operation_methods[element_id] = method.upper()
        operation_by_uri[route.split("_", 1)[-1]] = element_id
        add_relationship(
            relations, "AssignmentRelationship", gateway_id, element_id, f"gateway-operation:{about}", "exposes"
        )

    # Business processes inferred by the process-mining part of the ontology.
    process_ids: list[str] = []
    process_by_name: dict[str, str] = {}
    for node in by_type["process-view#Process"]:
        about = node.attrib[f"{{{RDF}}}about"]
        # Process individuals also carry derived labels such as
        # ``domain:...``.  Their identifier is the stable process name.
        name = local(about)
        element_id = add_element(business, "BusinessProcess", name, f"process:{about}")
        elements[f"process:{about}"] = element_id
        process_ids.append(element_id)
        process_by_name[name] = element_id

    # Data is modeled at domain/entity granularity, avoiding API payload fields.
    domain_ids: dict[str, str] = {}
    for node in by_type["data-relation-view#DataDomain"]:
        about = node.attrib[f"{{{RDF}}}about"]
        domain_ids[about] = add_element(other, "Grouping", f"Data domain: {node_name(node)}", f"domain:{about}")

    data_ids: list[str] = []
    data_by_domain_entity: dict[tuple[str, str], str] = {}
    for node in by_type["data-relation-view#CorrelatedDataObjects"]:
        domain = next(iter(node_resources(node, "CorrelatedDomain")), "")
        entity = next(iter(node_resources(node, "CorrelatedEntity")), "")
        if not domain or not entity:
            continue
        name = f"{local(domain)}: {local(entity)}"
        element_id = add_element(application, "DataObject", name, f"data:{domain}:{entity}")
        data_by_domain_entity[(local(domain), local(entity))] = element_id
        data_ids.append(element_id)
        if domain in domain_ids:
            add_relationship(
                relations, "CompositionRelationship", domain_ids[domain], element_id,
                f"domain-data:{domain}:{entity}", "contains"
            )

    # The CorrelatedDataObjects assertions state that an entity belongs to a
    # process/domain.  Add a direct business-layer access relationship so the
    # business-process/data view remains meaningful even without API services.
    for (domain_name, _entity_name), data_id in data_by_domain_entity.items():
        process_id = process_by_name.get(domain_name)
        if process_id:
            add_relationship(
                relations,
                "AccessRelationship",
                process_id,
                data_id,
                f"process-data:{process_id}:{data_id}",
                "uses data",
                {"accessType": "1"},
            )

    # Attach each operation to its data object based on the structured API URI.
    for uri, operation_id in operation_by_uri.items():
        parts = [part for part in uri.split("/") if part]
        if len(parts) >= 4:
            domain, entity = parts[1], parts[3]
            data_id = data_by_domain_entity.get((domain, entity))
            if data_id:
                access_type = "1" if operation_methods[operation_id] == "GET" else "2"
                add_relationship(
                    relations, "AccessRelationship", operation_id, data_id,
                    f"operation-data:{operation_id}:{data_id}", "reads" if access_type == "1" else "writes",
                    {"accessType": access_type},
                )
        # A similarly named mined process receives the application service.
        for process_key, process_id in elements.items():
            if process_key.startswith("process:") and local(process_key.removeprefix("process:")) in uri:
                add_relationship(
                    relations, "ServingRelationship", operation_id, process_id,
                    f"operation-process:{operation_id}:{process_id}", "supports"
                )

    # Each APICall is mediated by a consumer, destination, and resource.  We
    # aggregate those 392 call events into consumer -> destination flow counts.
    call_participants: dict[str, set[str]] = defaultdict(set)
    participant_types = {"core#ConsumerApp", "core#ServiceDestination"}
    for node_type in participant_types:
        for node in by_type[node_type]:
            participant = node.attrib[f"{{{RDF}}}about"]
            for call in node_resources(node, "participatedIn"):
                call_participants[call].add(participant)
    destination_flows: Counter[tuple[str, str]] = Counter()
    for participants in call_participants.values():
        consumers = [value for value in participants if value in elements and value in by_about and first_type(by_about[value]) == "core#ConsumerApp"]
        destinations = [value for value in participants if value in elements and value in by_about and first_type(by_about[value]) == "core#ServiceDestination"]
        for consumer in consumers:
            for destination in destinations:
                destination_flows[(consumer, destination)] += 1
    for (consumer, destination), count in destination_flows.items():
        add_relationship(
            relations, "FlowRelationship", gateway_id, elements[destination],
            f"gateway-destination:{consumer}:{destination}", "routes",
            {"frequency": count, "sourceApplication": node_name(by_about[consumer])},
        )

    # Process-mining correlations become aggregated operation flows.  Labels
    # keep both endpoints in a single asserted fact.
    transition_counts: Counter[tuple[str, str]] = Counter()
    expression = re.compile(r"antecedent operation:\s*(.+?)\s+consequent:\s*(.+?)(?:\s+partner:|$)")
    for node in by_type["process-view#APIActivitiesConnection"]:
        for label in [
            child.text.strip() for child in node
            if child.tag == f"{{{RDFS}}}label" and child.text
        ]:
            match = expression.search(label)
            if match:
                source, target = match.groups()
                if source in elements and target in elements:
                    transition_counts[(source, target)] += 1
    for (source, target), count in transition_counts.items():
        add_relationship(
            relations, "FlowRelationship", elements[source], elements[target],
            f"operation-flow:{source}:{target}", "frequently followed by", {"frequency": count}
        )

    relationship_nodes = list(relations.findall("element"))
    add_view(
        views,
        "API Gateway Overview",
        consumer_ids + [gateway_id] + destination_ids,
        relationship_nodes,
    )
    add_view(views, "API Operations", operation_ids, relationship_nodes)
    add_view(
        views,
        "Business Processes and Data",
        process_ids + list(domain_ids.values()) + data_ids,
        relationship_nodes,
    )
    return model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="RDF/XML OWL knowledge graph")
    parser.add_argument("output", type=Path, help="ArchiMate .archimate output path")
    args = parser.parse_args()

    model = build_model(parse_owl(args.input))
    ET.indent(model, space="  ")
    ET.ElementTree(model).write(args.output, encoding="utf-8", xml_declaration=True)
    print("Wrote ArchiMate model.")


if __name__ == "__main__":
    main()
