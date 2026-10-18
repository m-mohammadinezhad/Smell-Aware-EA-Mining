"""
Detector for the 42 Enterprise Architecture smells that have an explicit
Cypher detection rule in the RWTH Aachen EA Smells catalogue.

Usage:
    python ea_smell_catalog_detector.py MODELS_FOLDER --out output_folder

The input parser supports Archi / ArchiMate Tool .archimate files, in which
both architectural elements and relationships are stored as <element> nodes.
Each detected instance is emitted as evidence (element IDs and names), rather
than only as an aggregate score.
"""
from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

import networkx as nx
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter


CATALOG_URL = "https://swc-public.pages.rwth-aachen.de/smells/ea-smells/"
BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MODELS = [
    BASE_DIR / "04_methods" / "KDM2ArchiMate" / "KDM2ArchiMate_repaired.archimate",
    BASE_DIR / "04_methods" / "owl_to_archimate" / "1.archimate",
    BASE_DIR / "03_data" / "my-sample" / "test1.archimate",
    BASE_DIR / "03_data" / "my-sample" / "all-smells.archimate",
]
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "ea_smell_output"
# Configure the input and output folders here. The script does not read
# command-line arguments.
#MODELS_FOLDER = BASE_DIR / "03_data" / "my-sample"

#MODELS_FOLDER = BASE_DIR / "03_data" / "owl_to_archimate"
#MODELS_FOLDER = BASE_DIR / "03_data" / "sample"
#MODELS_FOLDER = BASE_DIR / "03_data" / "eamodelset" / "eamodelset-selected"
MODELS_FOLDER = BASE_DIR / "03_data" / "eamodelset" / "eamodelset-archimate"
REPORT_OUTPUT = DEFAULT_OUTPUT

# The complete subset of catalogue entries whose `cypher` field is populated.
SUPPORTED_SMELLS = [
    "Chatty Service", "Combinatorial Explosion", "Cyclic Dependency",
    "Data Service", "Dead Component", "Deadlock", "Deficient Encapsulation",
    "Dense Structure", "Documentation", "Duplication", "Feature Envy",
    "Hub-like Modularization", "Incomplete Pairs", "Inconsistent Data",
    "Infinite Loop", "Junction named as element", "Lack of Synchronization",
    "Lazy Component", "Message Chain", "Missing Abstraction", "Missing Data",
    "Missing Negative Case", "Multifaceted Abstraction", "Nanoservices",
    "No Legacy", "Overgeneralization", "End Event Missing",
    "Start Event Missing", "Sand Pile", "Scattered Parasitic Functionality",
    "Shared Persistency", "Shotgun Surgery", "Stovepipe System",
    "Strict Layers Violation", "The God Object", "The word And in element name",
    "The word Or in element name", "Useless Test", "Vendor Lock-In",
    "Warm Bodies", "Weakened Modularity", "Wrong Cuts",
]

FLOW_RELS = {"triggeringrelationship", "flowrelationship"}
STRUCTURAL_RELS = {
    "aggregationrelationship", "realizationrelationship",
    "compositionrelationship", "assignmentrelationship",
}
SERVICE_TYPES = {"applicationservice", "businessservice", "technologyservice"}
PROCESS_TYPES = {"businessprocess", "applicationprocess", "technologyprocess"}
DATA_TYPES = {"dataobject", "businessobject", "artifact"}
INTERFACE_TYPES = {"applicationinterface", "businessinterface", "technologyinterface"}
EVENT_TYPES = {"businessevent", "applicationevent", "technologyevent", "event"}
GENERIC_ELEMENT_NAMES = {
    "business process", "application process", "technology process",
    "business service", "application service", "technology service",
    "business object", "data object", "application component",
    "business actor", "application interface", "technology interface",
}

# Initial rule-violation strengths from the proposed method.  These are
# deliberately configuration values: threshold-based smells are calibrated
# from their observed metric, while fixed values can later be tuned by experts.
BASE_RULE_STRENGTH = {
    # Structural, dependency, and modularity smells
    "Cyclic Dependency": 0.75,
    "Combinatorial Explosion": 0.75,
    "Dense Structure": 0.65,
    "Hub-like Modularization": 0.75,
    "Weakened Modularity": 0.70,
    "Message Chain": 0.65,
    "Missing Abstraction": 0.65,
    "Multifaceted Abstraction": 0.65,
    "Nanoservices": 0.60,
    "Scattered Parasitic Functionality": 0.70,
    "Shotgun Surgery": 0.75,
    "Stovepipe System": 0.70,
    "Wrong Cuts": 0.70,
    "Overgeneralization": 0.65,
    "The God Object": 0.80,

    # Data, service, encapsulation, and interface smells
    "Chatty Service": 0.65,
    "Data Service": 0.60,
    "Feature Envy": 0.65,
    "Shared Persistency": 0.70,
    "Deficient Encapsulation": 0.75,
    "Inconsistent Data": 0.70,
    "Missing Data": 0.65,
    "Sand Pile": 0.60,
    "Lazy Component": 0.45,
    "Vendor Lock-In": 0.70,
    "Warm Bodies": 0.50,

    # Lifecycle, process, and behavioral smells
    "Dead Component": 0.50,
    "Deadlock": 0.80,
    "Infinite Loop": 0.80,
    "Lack of Synchronization": 0.75,
    "Start Event Missing": 0.70,
    "End Event Missing": 0.70,
    "Missing Negative Case": 0.55,
    "Useless Test": 0.55,
    "Incomplete Pairs": 0.50,
    "No Legacy": 0.45,

    # Naming, documentation, and duplication smells
    "Duplicate Architectural Capability": 0.60,
    "Duplication": 0.60,
    "Documentation": 0.40,
    "Junction named as element": 0.40,
    "The word And in element name": 0.35,
    "The word Or in element name": 0.35,

    # Layering and governance smells
    "Layering Erosion": 0.75,
    "Strict Layers Violation": 0.75,
}


def clean_type(value: str | None) -> str:
    return (value or "").split(":")[-1].lower()


def infer_layer(node_type: str) -> str:
    if "business" in node_type:
        return "Business"
    if "application" in node_type:
        return "Application"
    if any(x in node_type for x in ("technology", "systemsoftware", "device", "node", "artifact")):
        return "Technology"
    if any(x in node_type for x in ("capability", "resource", "courseofaction", "strategy")):
        return "Strategy"
    if node_type in {"goal", "assessment", "requirement", "constraint", "stakeholder"}:
        return "Motivation"
    return "Other"


def read_model(path: Path) -> nx.MultiDiGraph:
    """Parse Archi Tool's file format, preserving node properties and relation types."""
    root = ET.parse(path).getroot()
    graph = nx.MultiDiGraph(model_name=root.attrib.get("name", path.stem))
    raw_relationships: list[ET.Element] = []

    for elem in root.iter():
        if clean_type(elem.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type")) in {
            "diagramobject", "connection", "archimatediagrammodel"
        }:
            continue
        if "source" in elem.attrib and "target" in elem.attrib:
            raw_relationships.append(elem)
            continue
        if elem.tag.split("}")[-1] != "element":
            continue
        node_id = elem.attrib.get("id") or elem.attrib.get("identifier")
        node_type = clean_type(elem.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type"))
        if not node_id or not node_type:
            continue
        props = {p.attrib.get("key", "").lower(): p.attrib.get("value", "")
                 for p in elem.findall("./property")}
        graph.add_node(
            node_id,
            name=elem.attrib.get("name", ""),
            type=node_type,
            layer=infer_layer(node_type),
            documentation=elem.attrib.get("documentation", ""),
            properties=props,
        )

    for rel in raw_relationships:
        source, target = rel.attrib.get("source"), rel.attrib.get("target")
        if source not in graph or target not in graph:
            continue
        rel_type = clean_type(rel.attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type"))
        graph.add_edge(
            source, target, key=rel.attrib.get("id", ""),
            type=rel_type, name=rel.attrib.get("name", "")
        )
    return graph


def node_type(g: nx.MultiDiGraph, node: str) -> str:
    return g.nodes[node]["type"]


def node_name(g: nx.MultiDiGraph, node: str) -> str:
    return g.nodes[node].get("name") or node


def relation_type(data: dict[str, Any]) -> str:
    return data.get("type", "")


def neighbours(g: nx.MultiDiGraph, node: str) -> set[str]:
    return set(g.predecessors(node)) | set(g.successors(node))


def edges_between(g: nx.MultiDiGraph, a: str, b: str) -> Iterable[dict[str, Any]]:
    for _, _, data in g.edges(a, data=True):
        # MultiDiGraph edges(a) only returns outgoing edges; reverse checked separately.
        yield data
    for _, _, data in g.in_edges(a, data=True):
        yield data


def undirected(g: nx.MultiDiGraph) -> nx.Graph:
    h = nx.Graph()
    h.add_nodes_from(g.nodes(data=True))
    h.add_edges_from((u, v) for u, v in g.edges())
    return h


def directed_simple(g: nx.MultiDiGraph, allowed: set[str] | None = None) -> nx.DiGraph:
    h = nx.DiGraph()
    h.add_nodes_from(g.nodes(data=True))
    for u, v, data in g.edges(data=True):
        if allowed is None or relation_type(data) in allowed:
            h.add_edge(u, v)
    return h


def has_relation(g: nx.MultiDiGraph, a: str, b: str, allowed: set[str] | None = None) -> bool:
    for u, v, data in list(g.out_edges(a, data=True)) + list(g.in_edges(a, data=True)):
        if (u == a and v == b) or (u == b and v == a):
            if allowed is None or relation_type(data) in allowed:
                return True
    return False


def related_of_type(g: nx.MultiDiGraph, node: str, types: set[str],
                    rel_types: set[str] | None = None) -> list[str]:
    answer = []
    for other in neighbours(g, node):
        if node_type(g, other) in types and has_relation(g, node, other, rel_types):
            answer.append(other)
    return answer


def paths_to_type(g: nx.MultiDiGraph, start: str, end_types: set[str],
                  max_depth: int, allowed: set[str] = FLOW_RELS) -> list[list[str]]:
    h = directed_simple(g, allowed)
    paths = []
    stack = [(start, [start])]
    while stack:
        node, path = stack.pop()
        if len(path) - 1 >= max_depth:
            continue
        for nxt in h.successors(node):
            if nxt in path:
                continue
            new_path = path + [nxt]
            if node_type(g, nxt) in end_types:
                paths.append(new_path)
            stack.append((nxt, new_path))
    return paths


def lower(value: Any) -> str:
    return str(value or "").lower()


def percentile(values: Iterable[int | float], fraction: float) -> float:
    """Return a linearly interpolated percentile without extra dependencies."""
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * fraction
    lower_index, upper_index = int(position), min(int(position) + 1, len(ordered) - 1)
    remainder = position - lower_index
    return ordered[lower_index] + (ordered[upper_index] - ordered[lower_index]) * remainder


def evidence(g: nx.MultiDiGraph, nodes: Iterable[str], detail: str = "") -> dict[str, Any]:
    ids = sorted(set(nodes))
    return {
        "element_ids": " | ".join(ids),
        "element_names": " | ".join(node_name(g, n) for n in ids),
        "detail": detail,
    }


def _metric_strength(smell: str, detail: str) -> float | None:
    """Estimate R(s) for threshold-based rules from detector evidence."""
    text = lower(detail)
    patterns = {
        "Chatty Service": (r"interactions=(\d+(?:\.\d+)?)", 3.0),
        "Message Chain": (r"length=(\d+(?:\.\d+)?)", 3.0),
        "Shared Persistency": (r"accessors=(\d+(?:\.\d+)?)", 2.0),
        "Nanoservices": (r"count=(\d+(?:\.\d+)?)", 3.0),
        "Shotgun Surgery": (r"abstractions=(\d+(?:\.\d+)?)", 3.0),
        "Duplication": (r"similarity=(\d+(?:\.\d+)?)", 0.60),
    }
    rule = patterns.get(smell)
    if rule is None:
        return None
    match = re.search(rule[0], text)
    if not match:
        return None
    value, threshold = float(match.group(1)), rule[1]
    if smell == "Duplication":
        return max(0.0, min(1.0, value))
    # Normalize the observed metric against twice the threshold.  This makes
    # a value exactly at the detection threshold a moderate violation (0.5),
    # while a value at or above twice the threshold reaches the maximum (1.0).
    return max(0.0, min(1.0, value / max(2.0 * threshold, 1.0)))


def add_severity(g: nx.MultiDiGraph, smell: str, item: dict[str, Any]) -> dict[str, Any]:
    """Attach R(s), C(s), Severity(s), and final severity class to evidence."""
    ids = [node_id for node_id in item.get("element_ids", "").split(" | ") if node_id in g]
    degrees = [g.degree(node_id) for node_id in ids]
    max_degree = max((g.degree(node_id) for node_id in g), default=0)
    structural_importance = (
        sum(degrees) / len(degrees) / max_degree if degrees and max_degree else 0.0
    )
    observed_strength = _metric_strength(smell, item.get("detail", ""))
    rule_strength = (
        observed_strength
        if observed_strength is not None
        else BASE_RULE_STRENGTH.get(smell, 0.60)
    )
    severity = round(0.7 * rule_strength + 0.3 * structural_importance, 4)
    level = "High" if severity >= 0.70 else "Medium" if severity >= 0.40 else "Low"
    item.update({
        "rule_strength": round(rule_strength, 4),
        "structural_importance": round(structural_importance, 4),
        "severity": severity,
        "severity_level": level,
    })
    return item


def detect(g: nx.MultiDiGraph) -> dict[str, list[dict[str, Any]]]:
    """Run every catalogue detector through its dedicated smell module."""
    from smells.catalog_registry import DETECTORS

    return {smell_name: DETECTORS[smell_name](g) for smell_name in SUPPORTED_SMELLS}


def write_reports(input_paths: list[Path], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    filename_counts = Counter(path.name for path in input_paths)
    payload: dict[str, Any] = {
        "catalogue_source": CATALOG_URL,
        "supported_smell_count": len(SUPPORTED_SMELLS),
        "models": {},
    }
    total_models = len(input_paths)
    for model_index, path in enumerate(input_paths, start=1):
        remaining_models = total_models - model_index
        print(
            f"[{model_index}/{total_models}] Analysing {path.name} "
            f"({remaining_models} remaining)",
            flush=True,
        )
        model_name = path.name if filename_counts[path.name] == 1 else str(path)
        graph = read_model(path)
        results = detect(graph)
        # Severity is calculated per detected instance after all detectors
        # have produced their evidence.  The model parser above is unchanged.
        for smell, instances in results.items():
            results[smell] = [add_severity(graph, smell, item) for item in instances]
        model_result = {
            "nodes": graph.number_of_nodes(),
            "relationships": graph.number_of_edges(),
            "smells": results,
        }
        payload["models"][model_name] = model_result
        for smell in SUPPORTED_SMELLS:
            instances = results[smell]
            if instances:
                for index, item in enumerate(instances, 1):
                    rows.append({
                        "model": model_name, "smell": smell, "status": "Detected",
                        "instance": index, **item,
                    })
            else:
                rows.append({
                    "model": model_name, "smell": smell, "status": "Not detected",
                    "instance": "", "element_ids": "", "element_names": "", "detail": "",
                    "rule_strength": 0.0, "structural_importance": 0.0,
                    "severity": 0.0, "severity_level": "None",
                })
    with (output_dir / "ea_smell_results.json").open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    fields = [
        "model", "smell", "status", "instance", "element_ids", "element_names",
        "detail", "rule_strength", "structural_importance", "severity", "severity_level",
    ]
    try:
        with (output_dir / "ea_smell_results.csv").open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    except PermissionError:
        print("Warning: ea_smell_results.csv is open and was not updated; the Excel report will still be created.")
    summary = defaultdict(lambda: {"detected_smell_types": 0, "instances": 0})
    for row in rows:
        if row["status"] == "Detected":
            summary[row["model"]]["instances"] += 1
            if row["instance"] == 1:
                summary[row["model"]]["detected_smell_types"] += 1
    with (output_dir / "ea_smell_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(dict(summary), handle, ensure_ascii=False, indent=2)

    workbook = Workbook()
    results_sheet = workbook.active
    results_sheet.title = "EA Smell Results"
    results_sheet.append(fields)
    for row in rows:
        results_sheet.append([row.get(field, "") for field in fields])

    header_fill = PatternFill(fill_type="solid", fgColor="1F4E78")
    for cell in results_sheet[1]:
        cell.font = Font(color="FFFFFF", bold=True)
        cell.fill = header_fill
    results_sheet.freeze_panes = "A2"
    results_sheet.auto_filter.ref = results_sheet.dimensions
    for column_index, field in enumerate(fields, 1):
        longest = max(len(str(field)), *(len(str(row.get(field, ""))) for row in rows))
        results_sheet.column_dimensions[get_column_letter(column_index)].width = min(longest + 2, 50)

    summary_sheet = workbook.create_sheet("Summary")
    summary_fields = ["model", "detected_smell_types", "instances"]
    summary_sheet.append(summary_fields)
    for model, values in summary.items():
        summary_sheet.append([model, values["detected_smell_types"], values["instances"]])
    for cell in summary_sheet[1]:
        cell.font = Font(color="FFFFFF", bold=True)
        cell.fill = header_fill
    summary_sheet.freeze_panes = "A2"
    summary_sheet.auto_filter.ref = summary_sheet.dimensions
    for column_index, field in enumerate(summary_fields, 1):
        longest = max(len(str(field)), *(len(str(row[column_index - 1])) for row in summary_sheet.iter_rows(min_row=2, values_only=True)))
        summary_sheet.column_dimensions[get_column_letter(column_index)].width = min(longest + 2, 35)

    workbook.save(output_dir / "ea_smell_results.xlsx")


def find_model_files(models_dir: Path) -> list[Path]:
    """Recursively return all ArchiMate model files below ``models_dir``."""
    if not models_dir.is_dir():
        raise NotADirectoryError(f"Models folder not found: {models_dir}")

    model_files = sorted(
        path for path in models_dir.rglob("*")
        if path.is_file() and path.suffix.lower() == ".archimate"
    )
    if not model_files:
        raise FileNotFoundError(
            f"No .archimate model files were found in: {models_dir.resolve()}"
        )
    return model_files


if __name__ == "__main__":
    input_paths = find_model_files(MODELS_FOLDER)
    write_reports(input_paths, REPORT_OUTPUT)
    print(
        f"Analysed {len(input_paths)} model(s) from "
        f"{MODELS_FOLDER.resolve()}; reports written to {REPORT_OUTPUT.resolve()}"
    )
