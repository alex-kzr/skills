"""Read-only, fail-closed validator for a repository's generated project-local
feature-pipeline and Graphify configuration.

This module never repairs, normalizes, or creates anything in the target tree:
a validation failure is *evidence of a generator defect*, not something to fix
here. It only reads files and runs read-only Git plumbing
(``git rev-parse`` / ``git ls-files`` / ``git check-ignore``). It never runs the
Graphify wrapper, never installs a dependency, and never creates version-control
history. See ``../SKILL.md`` and ``../references/project-profile-contract.md``
for the full contract; the contract *values* (task types, the five Graphify
outputs, the installer denylist, the ignore line) are imported from
``setup_project`` rather than restated here.

Usage::

    python validate_project_setup.py --project-root <repo> \\
        --agents-root <agents checkout> --core-root <feature-pipeline-skill>
    python validate_project_setup.py --self-test
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple

import setup_project

# -- contract constants, reused (never re-literalled) -----------------------

TASK_TYPES = setup_project.TASK_TYPES
SHELL_TOKENS = setup_project.SHELL_TOKENS
GITIGNORE_LINE = setup_project.GITIGNORE_LINE
GRAPHIFY_WORKSPACE = setup_project.GRAPHIFY_WORKSPACE
GRAPHIFY_SCAN_ROOT = setup_project.GRAPHIFY_SCAN_ROOT
GRAPHIFY_OUT_DIR = setup_project.GRAPHIFY_OUT_DIR
REQUIRED_GRAPHIFY_OUTPUTS = list(setup_project.REQUIRED_GRAPHIFY_OUTPUTS)
FORBIDDEN_GRAPHIFY_COMMANDS = list(setup_project.FORBIDDEN_GRAPHIFY_COMMANDS)
SCHEMA_VERSION = setup_project.SCHEMA_VERSION

FP_CONFIG = "tools/feature-pipeline/config"
PROFILE_REL = f"{FP_CONFIG}/pipeline.profile.json"
INTEGRATIONS_REL = f"{FP_CONFIG}/integrations.json"
CHECKS_REL = f"{FP_CONFIG}/checks.json"
README_REL = "tools/feature-pipeline/README.md"
GRAPHIFYIGNORE_REL = setup_project.ROOT_GRAPHIFYIGNORE_REL  # repository-root .graphifyignore
GRAPHIFY_PROJECT_CONFIG_REL = "tools/graphify/config/graphify.project.json"

#: A ``.gitignore`` rule that would hide the whole tracked ``tools/graphify/``
#: tree, not just its generated output.
BROAD_GRAPHIFY_IGNORE = frozenset(
    {
        "tools/graphify",
        "tools/graphify/",
        "/tools/graphify",
        "/tools/graphify/",
        "tools/graphify/*",
        "/tools/graphify/*",
        "tools/graphify/**",
        "/tools/graphify/**",
        "tools/graphify/**/*",
    }
)


class Finding(NamedTuple):
    """One stable, machine-readable validation defect."""

    code: str
    detail: str

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"{self.code}: {self.detail}"


_MISSING = object()


# -- read-only snapshot ----------------------------------------------------


def _snapshot(root: Path) -> "dict[str, str]":
    """Map every non-``.git`` file under ``root`` to its content hash."""
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if ".git" in rel.parts:
            continue
        if path.is_file():
            out[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


# -- path rules (mirrors setup_project._rel_path, with distinct codes) -----


def _path_finding(value: Any, field: str) -> "Finding | None":
    if not isinstance(value, str) or not value:
        return Finding("E_SCHEMA", f"{field} must be a non-empty string")
    if "\\" in value:
        return Finding("E_PATH_BACKSLASH", f"{field} uses '\\' separators: {value!r}")
    if (len(value) >= 2 and value[1] == ":" and value[0].isalpha()) or value.startswith(
        ("/", "~")
    ):
        return Finding("E_PATH_ABSOLUTE", f"{field} is not anchor-relative: {value!r}")
    if any(part == ".." for part in value.split("/")):
        return Finding("E_PATH_ESCAPE", f"{field} traverses outside its anchor: {value!r}")
    return None


def _norm_rel(value: str) -> str:
    return "/".join(p for p in value.split("/") if p not in ("", "."))


# -- git plumbing (read-only) --------------------------------------------


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
    )


def _is_work_tree(root: Path) -> bool:
    proc = _git(root, "rev-parse", "--is-inside-work-tree")
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _tracked(root: Path, pathspec: str) -> "list[str]":
    proc = _git(root, "ls-files", "-z", "--", pathspec)
    if proc.returncode != 0:
        return []
    return [entry for entry in proc.stdout.split("\0") if entry]


def _is_ignored(root: Path, rel: str) -> bool:
    # --no-index: evaluate the ignore rules even for a path Git already tracks,
    # so a rule that *would* hide tracked configuration is still caught.
    return _git(root, "check-ignore", "--no-index", "-q", "--", rel).returncode == 0


# -- JSON loading -------------------------------------------------------


def _load_json(
    root: Path, rel: str, findings: "list[Finding]"
) -> "Any | None":
    path = root / rel
    if not path.is_file():
        findings.append(Finding("E_STRUCTURE", f"required file is missing: {rel}"))
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as err:
        findings.append(Finding("E_JSON_SYNTAX", f"{rel} is not valid JSON: {err}"))
        return None


def _require(
    obj: Any, key: str, field: str, findings: "list[Finding]"
) -> Any:
    if not isinstance(obj, dict) or key not in obj:
        findings.append(Finding("E_SCHEMA", f"{field} is missing required key {key!r}"))
        return _MISSING
    return obj[key]


# -- individual sections ------------------------------------------------


def _validate_profile(
    root: Path, core_rel_expected: str, agents_rel_expected: str, findings: "list[Finding]"
) -> None:
    profile = _load_json(root, PROFILE_REL, findings)
    if profile is None:
        return
    if not isinstance(profile, dict):
        findings.append(Finding("E_SCHEMA", f"{PROFILE_REL} must be a JSON object"))
        return

    if profile.get("schema_version") != SCHEMA_VERSION:
        findings.append(
            Finding(
                "E_SCHEMA",
                f"{PROFILE_REL} schema_version must be {SCHEMA_VERSION}, got "
                f"{profile.get('schema_version')!r}",
            )
        )
    if "checks" in profile:
        findings.append(
            Finding(
                "E_SCHEMA",
                f"{PROFILE_REL} must not carry an inline 'checks' array; checks live "
                "in checks.json",
            )
        )
    _require(profile, "project", PROFILE_REL, findings)

    anchors = _require(profile, "anchors", PROFILE_REL, findings)
    if isinstance(anchors, dict):
        for key, expected in (
            ("agents_root", agents_rel_expected),
            ("core_root", core_rel_expected),
        ):
            value = _require(anchors, key, f"{PROFILE_REL}.anchors", findings)
            if value is _MISSING:
                continue
            bad = _path_finding(value, f"{PROFILE_REL}.anchors.{key}")
            if bad:
                findings.append(bad)
                continue
            if expected is not None and _norm_rel(value) != _norm_rel(expected):
                findings.append(
                    Finding(
                        "E_ANCHOR_MISMATCH",
                        f"{PROFILE_REL}.anchors.{key} is {value!r} but the supplied "
                        f"anchor resolves to {expected!r}",
                    )
                )

    routing = _require(profile, "task_routing", PROFILE_REL, findings)
    if isinstance(routing, list):
        if not routing:
            findings.append(Finding("E_SCHEMA", f"{PROFILE_REL}.task_routing is empty"))
        for i, entry in enumerate(routing):
            field = f"{PROFILE_REL}.task_routing[{i}]"
            if not isinstance(entry, dict):
                findings.append(Finding("E_SCHEMA", f"{field} must be an object"))
                continue
            task_type = entry.get("task_type")
            if task_type not in TASK_TYPES:
                findings.append(
                    Finding("E_TASK_TYPE", f"{field}.task_type {task_type!r} is not approved")
                )
            bad = _path_finding(entry.get("working_root"), f"{field}.working_root")
            if bad:
                findings.append(bad)
    elif routing is not _MISSING:
        findings.append(Finding("E_SCHEMA", f"{PROFILE_REL}.task_routing must be a list"))

    run_state = _require(profile, "run_state_path", PROFILE_REL, findings)
    if run_state is not _MISSING:
        bad = _path_finding(run_state, f"{PROFILE_REL}.run_state_path")
        if bad:
            findings.append(bad)
        else:
            norm = _norm_rel(run_state)
            core_norm = _norm_rel(core_rel_expected) if core_rel_expected else None
            if norm in ("", ".") or norm == "tools":
                findings.append(
                    Finding(
                        "E_RUN_STATE_PLACEMENT",
                        f"run_state_path {run_state!r} must name a concrete directory",
                    )
                )
            elif norm == GRAPHIFY_OUT_DIR or norm.startswith(GRAPHIFY_OUT_DIR + "/"):
                findings.append(
                    Finding(
                        "E_RUN_STATE_PLACEMENT",
                        f"run_state_path {run_state!r} is inside generated Graphify output",
                    )
                )
            elif core_norm and (norm == core_norm or norm.startswith(core_norm + "/")):
                findings.append(
                    Finding(
                        "E_RUN_STATE_PLACEMENT",
                        f"run_state_path {run_state!r} is inside the portable core",
                    )
                )

    roles = _require(profile, "roles", PROFILE_REL, findings)
    if isinstance(roles, list):
        if not roles:
            findings.append(Finding("E_ROLE_GRANTS", f"{PROFILE_REL}.roles is empty"))
        for i, entry in enumerate(roles):
            field = f"{PROFILE_REL}.roles[{i}]"
            if not isinstance(entry, dict) or not entry.get("role"):
                findings.append(Finding("E_ROLE_GRANTS", f"{field}.role is missing"))
                continue
            grants = entry.get("min_grants")
            if (
                not isinstance(grants, list)
                or not grants
                or not all(isinstance(g, str) and g for g in grants)
            ):
                findings.append(
                    Finding(
                        "E_ROLE_GRANTS",
                        f"{field}.min_grants must be a non-empty list of grant names",
                    )
                )
    elif roles is not _MISSING:
        findings.append(Finding("E_SCHEMA", f"{PROFILE_REL}.roles must be a list"))


def _validate_checks(root: Path, findings: "list[Finding]") -> None:
    path = root / CHECKS_REL
    if not path.is_file():
        return  # checks.json is only written when at least one check is declared
    checks_doc = _load_json(root, CHECKS_REL, findings)
    if checks_doc is None:
        return
    if not isinstance(checks_doc, dict) or checks_doc.get("schema_version") != SCHEMA_VERSION:
        findings.append(
            Finding("E_SCHEMA", f"{CHECKS_REL} schema_version must be {SCHEMA_VERSION}")
        )
    entries = checks_doc.get("checks") if isinstance(checks_doc, dict) else None
    if not isinstance(entries, list):
        findings.append(Finding("E_SCHEMA", f"{CHECKS_REL}.checks must be a list"))
        return
    for i, entry in enumerate(entries):
        field = f"{CHECKS_REL}.checks[{i}]"
        if not isinstance(entry, dict):
            findings.append(Finding("E_SCHEMA", f"{field} must be an object"))
            continue
        for key in ("stack", "name"):
            if not entry.get(key):
                findings.append(Finding("E_SCHEMA", f"{field}.{key} is missing"))
        argv = entry.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(t, str) and t for t in argv):
            findings.append(
                Finding("E_ARGV_TYPE", f"{field}.argv must be a non-empty list of strings")
            )
        else:
            for tok in argv:
                if any(sym in tok for sym in SHELL_TOKENS):
                    findings.append(
                        Finding(
                            "E_ARGV_SHELL",
                            f"{field}.argv contains a shell operator ({tok!r}); "
                            "provide a real argv list",
                        )
                    )
                    break
        bad = _path_finding(entry.get("cwd"), f"{field}.cwd")
        if bad:
            findings.append(bad)


def _validate_graphify(root: Path, findings: "list[Finding]") -> bool:
    """Return True when Graphify is enabled (so gitignore/tracking checks run)."""
    integrations = _load_json(root, INTEGRATIONS_REL, findings)
    if integrations is None:
        return False
    if not isinstance(integrations, dict):
        findings.append(Finding("E_SCHEMA", f"{INTEGRATIONS_REL} must be a JSON object"))
        return False
    if integrations.get("schema_version") != SCHEMA_VERSION:
        findings.append(
            Finding(
                "E_SCHEMA",
                f"{INTEGRATIONS_REL} schema_version must be {SCHEMA_VERSION}",
            )
        )
    if "graphify" not in integrations:
        return False

    block = integrations["graphify"]
    if not isinstance(block, dict):
        findings.append(Finding("E_SCHEMA", f"{INTEGRATIONS_REL}.graphify must be an object"))
        return True

    for rel in (GRAPHIFYIGNORE_REL, GRAPHIFY_PROJECT_CONFIG_REL):
        if not (root / rel).is_file():
            findings.append(Finding("E_STRUCTURE", f"required file is missing: {rel}"))

    if block.get("workspace") != GRAPHIFY_WORKSPACE:
        findings.append(
            Finding(
                "E_GRAPHIFY_WORKSPACE",
                f"{INTEGRATIONS_REL}.graphify.workspace must be {GRAPHIFY_WORKSPACE!r} "
                f"(the config/output home), got {block.get('workspace')!r}",
            )
        )

    if block.get("scan_root") != GRAPHIFY_SCAN_ROOT:
        findings.append(
            Finding(
                "E_GRAPHIFY_SCAN_ROOT",
                f"{INTEGRATIONS_REL}.graphify.scan_root must be {GRAPHIFY_SCAN_ROOT!r} "
                f"(Graphify indexes the whole repository), got {block.get('scan_root')!r}",
            )
        )

    # The root .graphifyignore is the scan-root indexing-rule file; it must at
    # least keep generated Graphify output out of the index.
    ignore_path = root / GRAPHIFYIGNORE_REL
    if ignore_path.is_file():
        ignore_lines = {
            line.strip()
            for line in ignore_path.read_text(encoding="utf-8").splitlines()
        }
        if GITIGNORE_LINE not in ignore_lines:
            findings.append(
                Finding(
                    "E_GRAPHIFYIGNORE_OUTPUT_RULE",
                    f"{GRAPHIFYIGNORE_REL} must contain {GITIGNORE_LINE!r} so generated "
                    "output is never indexed",
                )
            )

    wrapper_dir = block.get("wrapper_dir")
    bad = _path_finding(wrapper_dir, f"{INTEGRATIONS_REL}.graphify.wrapper_dir")
    if bad:
        findings.append(bad)
    else:
        norm = _norm_rel(wrapper_dir)
        if norm != GRAPHIFY_WORKSPACE and not norm.startswith(GRAPHIFY_WORKSPACE + "/"):
            findings.append(
                Finding(
                    "E_GRAPHIFY_WRAPPER_MISSING",
                    f"wrapper_dir {wrapper_dir!r} must live under {GRAPHIFY_WORKSPACE}/",
                )
            )
        else:
            wrapper_path = root / norm
            files = [p for p in wrapper_path.rglob("*") if p.is_file()] if wrapper_path.is_dir() else []
            if not files:
                findings.append(
                    Finding(
                        "E_GRAPHIFY_WRAPPER_MISSING",
                        f"wrapper directory {norm!r} does not exist or holds no files",
                    )
                )

    if block.get("expected_outputs") != REQUIRED_GRAPHIFY_OUTPUTS:
        findings.append(
            Finding(
                "E_GRAPHIFY_OUTPUTS",
                f"{INTEGRATIONS_REL}.graphify.expected_outputs must be exactly the five "
                f"required outputs in order: {REQUIRED_GRAPHIFY_OUTPUTS}",
            )
        )
    if block.get("diff_policy") != "tracked-empty":
        findings.append(
            Finding(
                "E_GRAPHIFY_DIFF_POLICY",
                f"{INTEGRATIONS_REL}.graphify.diff_policy must be 'tracked-empty', got "
                f"{block.get('diff_policy')!r}",
            )
        )
    if block.get("forbidden") != FORBIDDEN_GRAPHIFY_COMMANDS:
        findings.append(
            Finding(
                "E_GRAPHIFY_FORBIDDEN",
                f"{INTEGRATIONS_REL}.graphify.forbidden must be exactly the installer "
                f"denylist: {FORBIDDEN_GRAPHIFY_COMMANDS}",
            )
        )
    return True


def _validate_gitignore(root: Path, findings: "list[Finding]") -> bool:
    """Return True when a broad ``tools/graphify/`` ignore rule was found."""
    path = root / ".gitignore"
    if not path.is_file():
        findings.append(
            Finding("E_GITIGNORE_MISSING_RULE", f"root .gitignore is missing {GITIGNORE_LINE!r}")
        )
        return False
    lines = {line.strip() for line in path.read_text(encoding="utf-8").splitlines()}
    if GITIGNORE_LINE not in lines:
        findings.append(
            Finding(
                "E_GITIGNORE_MISSING_RULE",
                f"root .gitignore must contain exactly {GITIGNORE_LINE!r}",
            )
        )
    broad = sorted(lines & BROAD_GRAPHIFY_IGNORE)
    if broad:
        findings.append(
            Finding(
                "E_GITIGNORE_BROAD_RULE",
                f"root .gitignore rule(s) {broad} hide the whole tracked tools/graphify/ tree",
            )
        )
    return bool(broad)


def _validate_git_boundaries(
    root: Path, graphify_enabled: bool, broad_ignore: bool, findings: "list[Finding]"
) -> None:
    tracked_out = _tracked(root, GRAPHIFY_OUT_DIR)
    if tracked_out:
        findings.append(
            Finding(
                "E_GIT_TRACKED_OUTPUT",
                f"generated Graphify output is tracked by Git: {sorted(tracked_out)}",
            )
        )

    must_stay_trackable = [PROFILE_REL, INTEGRATIONS_REL, README_REL]
    if (root / CHECKS_REL).is_file():
        must_stay_trackable.append(CHECKS_REL)
    # The root .graphifyignore lives outside tools/graphify/, so a broad
    # tools/graphify/ ignore rule cannot shadow it — always check it.
    if graphify_enabled:
        must_stay_trackable.append(GRAPHIFYIGNORE_REL)
    # A broad tools/graphify/ ignore rule is already reported as
    # E_GITIGNORE_BROAD_RULE; don't also re-report each file it shadows.
    if graphify_enabled and not broad_ignore:
        if (root / GRAPHIFY_PROJECT_CONFIG_REL).is_file():
            must_stay_trackable.append(GRAPHIFY_PROJECT_CONFIG_REL)
        wrapper = root / "tools/graphify/config"
        if wrapper.is_dir():
            must_stay_trackable.extend(
                p.relative_to(root).as_posix()
                for p in sorted(wrapper.rglob("*"))
                if p.is_file()
            )

    seen: set[str] = set()
    for rel in must_stay_trackable:
        if rel in seen:
            continue
        seen.add(rel)
        if (root / rel).exists() and _is_ignored(root, rel):
            findings.append(
                Finding(
                    "E_GIT_CONFIG_IGNORED",
                    f"tracked configuration/wrapper file is Git-ignored: {rel}",
                )
            )


# -- top-level -------------------------------------------------------


def validate(project_root: Path, agents_root: Path, core_root: Path) -> "list[Finding]":
    """Return every contract violation found. An empty list means valid.

    Pure read: no file under ``project_root`` is created or modified.
    """
    root = Path(project_root)
    findings: list[Finding] = []

    for rel in (PROFILE_REL, INTEGRATIONS_REL, README_REL):
        if not (root / rel).exists():
            findings.append(Finding("E_STRUCTURE", f"required file is missing: {rel}"))

    agents_rel = _rel_to(root, agents_root)
    core_rel = _rel_to(root, core_root)

    _validate_profile(root, core_rel, agents_rel, findings)
    _validate_checks(root, findings)
    graphify_enabled = _validate_graphify(root, findings)
    broad_ignore = _validate_gitignore(root, findings) if graphify_enabled else False
    _validate_git_boundaries(root, graphify_enabled, broad_ignore, findings)
    return findings


def _rel_to(root: Path, other: Path) -> "str | None":
    try:
        return Path(other).resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return None


def run_validation(
    project_root: "str | Path", agents_root: "str | Path", core_root: "str | Path"
) -> "list[Finding]":
    """Snapshot the tree, validate, and prove the pass was read-only."""
    root = Path(project_root)
    before = _snapshot(root)
    findings = validate(root, Path(agents_root), Path(core_root))
    after = _snapshot(root)
    if before != after:
        raise RuntimeError("validator mutated the target tree (this is a validator bug)")
    return findings


# -- self-test ------------------------------------------------------


def _self_test_input(wrapper_source: str) -> dict:
    return {
        "anchors": {
            "project_root": ".",
            "agents_root": ".agents",
            "core_root": "feature-pipeline-skill",
        },
        "task_routing": [
            {"task_type": "tooling", "working_root": "tools"},
            {"task_type": "docs", "working_root": "docs"},
        ],
        "technology_stacks": [
            {
                "stack": "python",
                "checks": [
                    {
                        "name": "unit",
                        "argv": ["uv", "run", "python", "-m", "unittest"],
                        "cwd": "feature-pipeline-skill",
                    }
                ],
            }
        ],
        "run_state_path": "tools/feature-pipeline/state",
        "roles": [{"role": "executor", "min_grants": ["read", "write"]}],
        "graphify": {
            "enabled": True,
            "wrapper_source": wrapper_source,
            "wrapper_destination": "tools/graphify/config/wrapper",
            "index_excludes": ["docs/fixtures"],
        },
    }


def self_test() -> int:
    """Build a valid fixture in a temp dir, prove it passes and stays read-only."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        project = tmp / "self-test-repo"
        (project / "docs").mkdir(parents=True)
        core = project / "feature-pipeline-skill" / "pipeline_core"
        core.mkdir(parents=True)
        (core / "profiles.py").write_text("# portable core\n", encoding="utf-8")
        (project / ".agents").mkdir()
        wrapper_src = tmp / "approved-wrapper"
        wrapper_src.mkdir()
        (wrapper_src / "build_graph.sh").write_text(
            '#!/bin/sh\nexport GRAPHIFY_OUT="$PWD/tools/graphify/graphify-out"\n'
            'exec graphify update . "$@"\n',
            encoding="utf-8",
        )

        if _git(project, "init", "-q").returncode != 0:
            print("self-test: could not 'git init' the fixture", file=sys.stderr)
            return 1

        setup_project.run_setup(
            _self_test_input(str(wrapper_src)),
            project_root=project,
            report_path="docs/setup-report.json",
            confirmed=True,
        )
        _git(project, "add", "-A")

        agents_root = project / ".agents"
        core_root = project / "feature-pipeline-skill"

        before = _snapshot(project)
        findings = validate(project, agents_root, core_root)
        after = _snapshot(project)
        pass_ok = not findings
        pass_readonly = before == after

        # Failing path must also be read-only.
        profile = project / PROFILE_REL
        profile.write_text("{ not valid json", encoding="utf-8")
        before_fail = _snapshot(project)
        fail_findings = validate(project, agents_root, core_root)
        after_fail = _snapshot(project)
        fail_detected = any(f.code == "E_JSON_SYNTAX" for f in fail_findings)
        fail_readonly = before_fail == after_fail

        print(
            json.dumps(
                {
                    "fixture": str(project),
                    "valid_fixture_passes": pass_ok,
                    "valid_path_read_only": pass_readonly,
                    "corrupt_fixture_detected": fail_detected,
                    "failing_path_read_only": fail_readonly,
                    "pass_findings": [f._asdict() for f in findings],
                },
                indent=2,
            )
        )
        return 0 if (pass_ok and pass_readonly and fail_detected and fail_readonly) else 1


# -- CLI ----------------------------------------------------------


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only validator for generated project-local feature-pipeline setup."
    )
    parser.add_argument("--project-root", help="Target repository to validate.")
    parser.add_argument("--agents-root", help="Shared agents repository checkout.")
    parser.add_argument("--core-root", help="Portable feature-pipeline-skill checkout.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Create a temporary valid fixture, validate it, and prove read-only.",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    if not (args.project_root and args.agents_root and args.core_root):
        print(
            "error: --project-root, --agents-root and --core-root are all required",
            file=sys.stderr,
        )
        return 2

    root = Path(args.project_root)
    if not root.is_dir():
        print(f"error: --project-root is not a directory: {root}", file=sys.stderr)
        return 2
    try:
        if not _is_work_tree(root):
            print(
                "error: --project-root is not inside a Git work tree; cannot check "
                "tracking boundaries",
                file=sys.stderr,
            )
            return 2
    except FileNotFoundError:
        print("error: git executable not found", file=sys.stderr)
        return 2

    try:
        findings = run_validation(root, args.agents_root, args.core_root)
    except RuntimeError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "project_root": str(root),
                "valid": not findings,
                "findings": [f._asdict() for f in findings],
            },
            indent=2,
        )
    )
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
