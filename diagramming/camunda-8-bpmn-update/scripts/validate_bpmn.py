#!/usr/bin/env python3
"""
Validate a BPMN 2.0 file against the OMG XSD schema plus Camunda 8 semantic rules.

Usage:
    python validate_bpmn.py <file.bpmn> [--strict]

Exit codes:
    0  — valid
    1  — validation errors found
    2  — usage / IO error

Options:
    --strict   Fail on warnings (Camunda 8 best-practice violations), not just errors.

Dependencies:
    Provided by the shared agents runtime (agents/runtime/python/base/.venv).
"""

import argparse
import os
import sys
from pathlib import Path


def _find_agents_root(start: Path) -> Path:
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / "skills").exists() and (parent / "runtime").exists():
            return parent
    raise RuntimeError("Cannot find agents root with both skills/ and runtime/")


def _add_runtime_site_packages() -> None:
    agents_root = _find_agents_root(Path(__file__))
    venv_dir = agents_root / "runtime" / "python" / "base" / ".venv"
    if os.name == "nt":
        site_packages = venv_dir / "Lib" / "site-packages"
    else:
        candidates = list((venv_dir / "lib").glob("python*/site-packages"))
        site_packages = candidates[0] if candidates else None
    if not site_packages or not site_packages.exists():
        raise RuntimeError(
            "Python runtime is not prepared. Expected site-packages at: "
            f"{site_packages}. Prepare agents/runtime/python/base/.venv first."
        )
    sys.path.insert(0, str(site_packages))


try:
    _add_runtime_site_packages()
    from lxml import etree
except (ImportError, RuntimeError) as e:
    print(f"ERROR: lxml is not available ({e}). "
          "Prepare agents/runtime/python/base/.venv (see runtime/README.md).", file=sys.stderr)
    sys.exit(2)

# Namespaces used in Camunda 8 / Zeebe BPMN files
NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "zeebe": "http://camunda.org/schema/zeebe/1.0",
    "modeler": "http://camunda.org/schema/modeler/1.0",
}

XSD_DIR = Path(__file__).parent.parent / "references" / "xsd"
BPMN20_XSD = XSD_DIR / "BPMN20.xsd"


def load_schema() -> etree.XMLSchema:
    """Load the BPMN 2.0 XSD, resolving imports relative to XSD_DIR."""
    parser = etree.XMLParser(load_dtd=False, no_network=True)

    # Build a custom resolver so schemaLocation="Semantic.xsd" works offline
    class LocalResolver(etree.Resolver):
        def resolve(self, url: str, id, context):
            candidate = XSD_DIR / Path(url).name
            if candidate.exists():
                return self.resolve_filename(str(candidate), context)
            return None

    xsd_parser = etree.XMLParser(load_dtd=False, no_network=True)
    xsd_parser.resolvers.add(LocalResolver())

    xsd_doc = etree.parse(str(BPMN20_XSD), xsd_parser)
    return etree.XMLSchema(xsd_doc)


def semantic_checks(tree: etree._ElementTree) -> tuple[list[str], list[str]]:
    """
    Camunda 8 semantic rules not covered by the OMG XSD.

    Returns (errors, warnings).
    - errors:   things Zeebe engine will reject at deployment
    - warnings: best-practice violations (only fail with --strict)
    """
    errors: list[str] = []
    warnings: list[str] = []
    root = tree.getroot()

    processes = root.findall(".//bpmn:process", NS)
    if not processes:
        errors.append("No <bpmn:process> element found.")
        return errors, warnings

    for proc in processes:
        pid = proc.get("id", "<unknown>")

        # Camunda 8 requires at least one executable process
        if proc.get("isExecutable", "false").lower() != "true":
            warnings.append(f"Process '{pid}': isExecutable is not 'true'.")

        # Service tasks must have a zeebe:taskDefinition or zeebe:calledDecision
        for st in proc.findall(".//bpmn:serviceTask", NS):
            sid = st.get("id", "<unknown>")
            ext = st.find("bpmn:extensionElements", NS)
            has_task_def = ext is not None and (
                ext.find("zeebe:taskDefinition", NS) is not None
                or ext.find("zeebe:calledDecision", NS) is not None
            )
            if not has_task_def:
                errors.append(
                    f"ServiceTask '{sid}' in process '{pid}': missing "
                    f"<zeebe:taskDefinition> or <zeebe:calledDecision> extension."
                )

        # Start events should have at most one outgoing flow (Zeebe MVP constraint)
        for se in proc.findall(".//bpmn:startEvent", NS):
            eid = se.get("id", "<unknown>")
            outgoing = se.findall("bpmn:outgoing", NS)
            if len(outgoing) > 1:
                warnings.append(
                    f"StartEvent '{eid}' in process '{pid}': "
                    f"has {len(outgoing)} outgoing flows (expected 1)."
                )

        # End events must not have outgoing flows
        for ee in proc.findall(".//bpmn:endEvent", NS):
            eid = ee.get("id", "<unknown>")
            outgoing = ee.findall("bpmn:outgoing", NS)
            if outgoing:
                errors.append(
                    f"EndEvent '{eid}' in process '{pid}': must not have outgoing flows."
                )

        # ExclusiveGateway: non-default flows should have conditions
        for gw in proc.findall(".//bpmn:exclusiveGateway", NS):
            gwid = gw.get("id", "<unknown>")
            default_flow = gw.get("default")
            for flow_id in [o.text for o in gw.findall("bpmn:outgoing", NS)]:
                if flow_id and flow_id != default_flow:
                    # Find the sequenceFlow
                    flow_el = root.find(
                        f'.//bpmn:sequenceFlow[@id="{flow_id}"]', NS
                    )
                    if flow_el is not None and flow_el.find("bpmn:conditionExpression", NS) is None:
                        warnings.append(
                            f"ExclusiveGateway '{gwid}': outgoing flow '{flow_id}' "
                            f"has no condition and is not the default flow."
                        )

        # Every sequenceFlow must have valid sourceRef / targetRef (basic ref check)
        element_ids: set[str] = set()
        for el in proc.iter():
            eid = el.get("id")
            if eid:
                element_ids.add(eid)
        for sf in proc.findall(".//bpmn:sequenceFlow", NS):
            for attr in ("sourceRef", "targetRef"):
                ref = sf.get(attr)
                if ref and ref not in element_ids:
                    errors.append(
                        f"SequenceFlow '{sf.get('id', '?')}': {attr}='{ref}' "
                        f"does not reference a known element in process '{pid}'."
                    )

    return errors, warnings


def validate(path: Path, strict: bool) -> bool:
    """Validate path; return True if valid (given strict flag)."""
    try:
        doc = etree.parse(str(path))
    except etree.XMLSyntaxError as exc:
        print(f"XML PARSE ERROR: {exc}")
        return False

    # --- XSD validation ---
    schema = load_schema()
    xsd_valid = schema.validate(doc)
    xsd_errors = list(schema.error_log)

    # --- Semantic checks ---
    sem_errors, sem_warnings = semantic_checks(doc)

    # --- Report ---
    has_errors = (not xsd_valid) or bool(sem_errors) or (strict and bool(sem_warnings))

    if xsd_errors:
        print("XSD ERRORS:")
        for e in xsd_errors:
            print(f"  line {e.line}: {e.message}")

    if sem_errors:
        print("SEMANTIC ERRORS (Camunda 8):")
        for e in sem_errors:
            print(f"  {e}")

    if sem_warnings:
        label = "WARNINGS (--strict treats as errors):" if strict else "WARNINGS:"
        print(label)
        for w in sem_warnings:
            print(f"  {w}")

    if not has_errors:
        print(f"OK: {path.name} is valid for Camunda 8.")

    return not has_errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a BPMN file for Camunda 8.")
    parser.add_argument("file", help="Path to the .bpmn file")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat Camunda 8 warnings as errors.",
    )
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(2)

    ok = validate(path, args.strict)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
