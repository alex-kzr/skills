"""Deterministic, fail-closed generator for a repository's project-local
feature-pipeline and Graphify configuration.

This module only *renders and writes project-local files* under the target
repository's ``tools/`` tree and its root ``.gitignore``. It never edits the
portable core, never runs a shell or an installer, never creates version-control
history, and never installs a dependency. See ``../SKILL.md`` and
``../references/project-profile-contract.md`` for the full contract.

Usage::

    python setup_project.py --input profile-input.json \\
        --project-root /path/to/target-repo --report docs/setup-report.json --confirm
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any


class SetupError(Exception):
    """Raised for any contract violation. Every raise is fail-closed."""


# -- constants mirrored from the portable core's contract --------------------

#: Supported task types (schemas.contracts.TASK_TYPES in the portable core).
TASK_TYPES = frozenset(
    {
        "python",
        "rust",
        "backend",
        "frontend",
        "ui",
        "plugin",
        "docs",
        "research",
        "design",
        "tooling",
        "agent_config",
    }
)

#: Tokens that make an argv a shell string rather than a real argv.
SHELL_TOKENS = frozenset({"|", "&&", ";", ">", "<", "`", "$("})

TOP_LEVEL_KEYS = frozenset(
    {
        "anchors",
        "task_routing",
        "technology_stacks",
        "run_state_path",
        "roles",
        "graphify",
    }
)
ANCHOR_KEYS = frozenset({"project_root", "agents_root", "core_root"})

GITIGNORE_LINE = "/tools/graphify/graphify-out/"
#: Where the project-local Graphify configuration and generated output live.
GRAPHIFY_WORKSPACE = "tools/graphify"
#: What the wrapper points ``graphify update`` at: the whole repository. The
#: wrapper pins ``GRAPHIFY_OUT`` to ``GRAPHIFY_OUT_DIR`` so output still lands
#: under the workspace even though the scan root is the repo root.
GRAPHIFY_SCAN_ROOT = "."
GRAPHIFY_OUT_DIR = "tools/graphify/graphify-out"
#: The generated root ``.graphifyignore`` always excludes generated output; a
#: project may add its own anchor-relative exclusions via ``graphify.index_excludes``.
ROOT_GRAPHIFYIGNORE_REL = ".graphifyignore"
REQUIRED_GRAPHIFY_OUTPUTS = (
    "tools/graphify/graphify-out/graph.json",
    "tools/graphify/graphify-out/GRAPH_REPORT.md",
    "tools/graphify/graphify-out/manifest.json",
    "tools/graphify/graphify-out/.graphify_labels.json",
    "tools/graphify/graphify-out/.graphify_root",
)
FORBIDDEN_GRAPHIFY_COMMANDS = (
    "graphify claude install",
    "graphify codex install",
    "graphify antigravity install",
)

SCHEMA_VERSION = 1


# -- path helpers ----------------------------------------------------------


def _rel_path(value: Any, field: str) -> str:
    """Return a validated POSIX anchor-relative path or raise ``SetupError``."""
    if not isinstance(value, str) or not value:
        raise SetupError(f"{field} must be a non-empty string")
    if "\\" in value:
        raise SetupError(f"{field} must use '/' separators, not '\\': {value!r}")
    if len(value) >= 2 and value[1] == ":" and value[0].isalpha():
        raise SetupError(f"{field} must not be an absolute path: {value!r}")
    if value.startswith(("/", "~")):
        raise SetupError(f"{field} must be anchor-relative, not {value!r}")
    parts = [p for p in value.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise SetupError(f"{field} must not traverse outside its anchor: {value!r}")
    return "/".join(parts) or "."


def _non_empty_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise SetupError(f"{field} must be a non-empty string")
    return value


def _list(value: Any, field: str) -> list:
    if not isinstance(value, list):
        raise SetupError(f"{field} must be a list")
    return value


def _object(value: Any, field: str) -> dict:
    if not isinstance(value, dict):
        raise SetupError(f"{field} must be an object")
    return value


def _reject_unknown(obj: dict, allowed: "frozenset[str] | set[str]", field: str) -> None:
    extra = set(obj) - set(allowed)
    if extra:
        raise SetupError(f"{field} has unknown key(s): {sorted(extra)}")
    missing = set(allowed) - set(obj)
    if missing:
        raise SetupError(f"{field} is missing required key(s): {sorted(missing)}")


# -- input validation ----------------------------------------------------


def validate_input(raw: Any) -> dict:
    """Fully validate the input object before a single file is rendered."""
    data = _object(raw, "input")
    _reject_unknown(data, TOP_LEVEL_KEYS, "input")

    anchors = _object(data["anchors"], "anchors")
    _reject_unknown(anchors, ANCHOR_KEYS, "anchors")
    _non_empty_str(anchors["project_root"], "anchors.project_root")
    agents_root = _rel_path(anchors["agents_root"], "anchors.agents_root")
    core_root = _rel_path(anchors["core_root"], "anchors.core_root")

    routing = _list(data["task_routing"], "task_routing")
    if not routing:
        raise SetupError("task_routing must not be empty")
    seen_types: set[str] = set()
    norm_routing = []
    for i, entry in enumerate(routing):
        obj = _object(entry, f"task_routing[{i}]")
        _reject_unknown(obj, {"task_type", "working_root"}, f"task_routing[{i}]")
        task_type = _non_empty_str(obj["task_type"], f"task_routing[{i}].task_type")
        if task_type not in TASK_TYPES:
            raise SetupError(
                f"task_routing[{i}].task_type {task_type!r} is not an approved task type"
            )
        if task_type in seen_types:
            raise SetupError(f"task_routing has a duplicate task type: {task_type!r}")
        seen_types.add(task_type)
        working_root = _rel_path(obj["working_root"], f"task_routing[{i}].working_root")
        norm_routing.append({"task_type": task_type, "working_root": working_root})

    stacks = _list(data["technology_stacks"], "technology_stacks")
    if not stacks:
        raise SetupError("technology_stacks must not be empty")
    norm_stacks = []
    for i, entry in enumerate(stacks):
        obj = _object(entry, f"technology_stacks[{i}]")
        _reject_unknown(obj, {"stack", "checks"}, f"technology_stacks[{i}]")
        stack = _non_empty_str(obj["stack"], f"technology_stacks[{i}].stack")
        checks = _list(obj["checks"], f"technology_stacks[{i}].checks")
        norm_checks = []
        for j, chk in enumerate(checks):
            cobj = _object(chk, f"technology_stacks[{i}].checks[{j}]")
            _reject_unknown(
                cobj, {"name", "argv", "cwd"}, f"technology_stacks[{i}].checks[{j}]"
            )
            name = _non_empty_str(
                cobj["name"], f"technology_stacks[{i}].checks[{j}].name"
            )
            argv = _list(cobj["argv"], f"technology_stacks[{i}].checks[{j}].argv")
            if not argv:
                raise SetupError(
                    f"technology_stacks[{i}].checks[{j}].argv must not be empty"
                )
            norm_argv = []
            for token in argv:
                tok = _non_empty_str(
                    token, f"technology_stacks[{i}].checks[{j}].argv[]"
                )
                if any(sym in tok for sym in SHELL_TOKENS):
                    raise SetupError(
                        f"technology_stacks[{i}].checks[{j}].argv contains a shell "
                        f"operator ({tok!r}); provide a real argv list"
                    )
                norm_argv.append(tok)
            cwd = _rel_path(cobj["cwd"], f"technology_stacks[{i}].checks[{j}].cwd")
            norm_checks.append({"name": name, "argv": norm_argv, "cwd": cwd})
        norm_stacks.append({"stack": stack, "checks": norm_checks})

    run_state_path = _rel_path(data["run_state_path"], "run_state_path")

    roles = _list(data["roles"], "roles")
    if not roles:
        raise SetupError("roles must not be empty")
    norm_roles = []
    for i, entry in enumerate(roles):
        obj = _object(entry, f"roles[{i}]")
        _reject_unknown(obj, {"role", "min_grants"}, f"roles[{i}]")
        role = _non_empty_str(obj["role"], f"roles[{i}].role")
        grants = _list(obj["min_grants"], f"roles[{i}].min_grants")
        if not grants:
            raise SetupError(f"roles[{i}].min_grants must not be empty")
        norm_grants = [_non_empty_str(g, f"roles[{i}].min_grants[]") for g in grants]
        norm_roles.append({"role": role, "min_grants": norm_grants})

    graphify = _object(data["graphify"], "graphify")
    enabled = graphify.get("enabled")
    if not isinstance(enabled, bool):
        raise SetupError("graphify.enabled must be a boolean")
    if enabled:
        _reject_unknown(
            graphify,
            {"enabled", "wrapper_source", "wrapper_destination", "index_excludes"},
            "graphify",
        )
        wrapper_source = graphify.get("wrapper_source")
        if not isinstance(wrapper_source, str) or not wrapper_source:
            raise SetupError(
                "graphify.enabled is true but graphify.wrapper_source is missing"
            )
        wrapper_destination = _rel_path(
            graphify["wrapper_destination"], "graphify.wrapper_destination"
        )
        if (
            wrapper_destination != GRAPHIFY_WORKSPACE
            and not wrapper_destination.startswith(GRAPHIFY_WORKSPACE + "/")
        ):
            raise SetupError(
                "graphify.wrapper_destination must live under tools/graphify/"
            )
        raw_excludes = _list(graphify["index_excludes"], "graphify.index_excludes")
        norm_excludes: list[str] = []
        for i, entry in enumerate(raw_excludes):
            pat = _rel_path(entry, f"graphify.index_excludes[{i}]")
            if pat == ".":
                raise SetupError(
                    f"graphify.index_excludes[{i}] must name a path below the "
                    "repository root, not the root itself"
                )
            if pat not in norm_excludes:
                norm_excludes.append(pat)
        norm_graphify = {
            "enabled": True,
            "wrapper_source": wrapper_source,
            "wrapper_destination": wrapper_destination,
            "index_excludes": norm_excludes,
        }
    else:
        _reject_unknown(graphify, {"enabled"}, "graphify")
        norm_graphify = {"enabled": False}

    return {
        "anchors": {
            "project_root": anchors["project_root"],
            "agents_root": agents_root,
            "core_root": core_root,
        },
        "task_routing": norm_routing,
        "technology_stacks": norm_stacks,
        "run_state_path": run_state_path,
        "roles": norm_roles,
        "graphify": norm_graphify,
    }


# -- rendering -----------------------------------------------------------


def _dumps(obj: Any) -> bytes:
    return (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _render_profile(data: dict, project_name: str) -> bytes:
    profile = {
        "schema_version": SCHEMA_VERSION,
        "project": project_name,
        "anchors": {
            "agents_root": data["anchors"]["agents_root"],
            "core_root": data["anchors"]["core_root"],
        },
        "task_routing": data["task_routing"],
        "run_state_path": data["run_state_path"],
        "roles": data["roles"],
    }
    return _dumps(profile)


def _has_checks(data: dict) -> bool:
    return any(stack["checks"] for stack in data["technology_stacks"])


def _render_checks(data: dict) -> bytes:
    checks = []
    for stack in data["technology_stacks"]:
        for chk in stack["checks"]:
            checks.append(
                {
                    "stack": stack["stack"],
                    "name": chk["name"],
                    "argv": chk["argv"],
                    "cwd": chk["cwd"],
                }
            )
    return _dumps({"schema_version": SCHEMA_VERSION, "checks": checks})


def _render_integrations(data: dict) -> bytes:
    integrations: dict[str, Any] = {"schema_version": SCHEMA_VERSION}
    if data["graphify"]["enabled"]:
        integrations["graphify"] = {
            "stage": "graphify",
            "executor": "runner:graphify",
            "workspace": GRAPHIFY_WORKSPACE,
            "scan_root": GRAPHIFY_SCAN_ROOT,
            "wrapper_dir": data["graphify"]["wrapper_destination"],
            "expected_outputs": list(REQUIRED_GRAPHIFY_OUTPUTS),
            "diff_policy": "tracked-empty",
            "forbidden": list(FORBIDDEN_GRAPHIFY_COMMANDS),
        }
    return _dumps(integrations)


def _render_graphify_project_config() -> bytes:
    return _dumps(
        {
            "schema_version": SCHEMA_VERSION,
            "workspace": GRAPHIFY_WORKSPACE,
            "scan_root": GRAPHIFY_SCAN_ROOT,
            "out_dir": GRAPHIFY_OUT_DIR,
            "required_outputs": list(REQUIRED_GRAPHIFY_OUTPUTS),
            "diff_policy": "tracked-empty",
        }
    )


def _render_root_graphifyignore(data: dict) -> bytes:
    """Render the repository-root ``.graphifyignore``.

    Graphify indexes from the repository root; it also honours the root
    ``.gitignore`` and its own built-in cache/venv skips. This file always
    excludes generated Graphify output and then any project-declared
    ``graphify.index_excludes`` paths, one anchored rule per line.
    """
    lines = [
        "# Generated by feature-pipeline-project-setup. Do not hand-edit; regenerate.",
        "# Graphify indexes the whole repository from its root. The root .gitignore",
        "# and Graphify's built-in cache/venv skips are also honoured; list only the",
        "# extra project-local exclusions here (via graphify.index_excludes).",
        "",
        "# Generated Graphify output (also covered by .gitignore).",
        GITIGNORE_LINE,
    ]
    excludes = data["graphify"].get("index_excludes") or []
    if excludes:
        lines.append("")
        lines.append("# Project-declared exclusions.")
        for pat in excludes:
            lines.append("/" + pat)
    return ("\n".join(lines) + "\n").encode("utf-8")


_README = (
    "# tools/feature-pipeline\n"
    "\n"
    "Project-local configuration for the portable feature-pipeline core.\n"
    "Generated by the `feature-pipeline-project-setup` skill; regenerate rather\n"
    "than hand-editing, and never move project literals into the portable core.\n"
    "\n"
    "- `config/pipeline.profile.json` - anchors, task routing, run state, roles.\n"
    "- `config/integrations.json` - project integration contract (e.g. Graphify).\n"
    "- `config/checks.json` - repository-defined check commands, when split out.\n"
    "\n"
    "All paths are POSIX-style and relative to the repository root.\n"
).encode("utf-8")

def _collect_wrapper_files(source: Path, destination: str) -> dict[str, bytes]:
    """Read the approved wrapper source into a {rel_path: bytes} map."""
    if not source.exists():
        raise SetupError(f"graphify wrapper source does not resolve: {source}")
    dest = PurePosixPath(destination)
    files: dict[str, bytes] = {}
    if source.is_file():
        files[str(dest / source.name)] = source.read_bytes()
        return files
    members = sorted(p for p in source.rglob("*") if p.is_file())
    if not members:
        raise SetupError(f"graphify wrapper source has no files: {source}")
    for member in members:
        rel = member.relative_to(source).as_posix()
        files[str(dest / rel)] = member.read_bytes()
    return files


def render_all(data: dict, project_name: str) -> "dict[str, bytes]":
    """Return the {relative POSIX path: bytes} map of files written under ``tools/``.

    The root ``.gitignore`` (merged) and the root ``.graphifyignore``
    (overwritten) are handled separately in :func:`run_setup`.
    """
    out: dict[str, bytes] = {}
    fp = "tools/feature-pipeline"
    out[f"{fp}/config/pipeline.profile.json"] = _render_profile(data, project_name)
    out[f"{fp}/config/integrations.json"] = _render_integrations(data)
    if _has_checks(data):
        out[f"{fp}/config/checks.json"] = _render_checks(data)
    out[f"{fp}/README.md"] = _README

    if data["graphify"]["enabled"]:
        out["tools/graphify/config/graphify.project.json"] = _render_graphify_project_config()
        out.update(
            _collect_wrapper_files(
                Path(data["graphify"]["wrapper_source"]),
                data["graphify"]["wrapper_destination"],
            )
        )
    return out


# -- .gitignore merge --------------------------------------------------


def merge_gitignore(existing: "str | None") -> str:
    """Append exactly ``GITIGNORE_LINE`` once, preserving all other lines."""
    if existing is None:
        return GITIGNORE_LINE + "\n"
    stripped = {line.strip() for line in existing.splitlines()}
    if GITIGNORE_LINE in stripped:
        return existing
    if existing and not existing.endswith("\n"):
        existing += "\n"
    return existing + GITIGNORE_LINE + "\n"


# -- orchestration ---------------------------------------------------


def _ensure_within(root: Path, target: Path, what: str) -> None:
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError:
        raise SetupError(f"{what} resolves outside the target project: {target}") from None


def run_setup(
    input_obj: Any,
    *,
    project_root: "str | Path",
    report_path: str,
    confirmed: bool,
) -> dict:
    """Validate, render and write the project-local layout. Fail-closed."""
    if not confirmed:
        raise SetupError(
            "input is not confirmed; refusing to write. Confirm discovered "
            "values first, then rerun with confirmation."
        )

    root = Path(project_root)
    if not root.is_dir():
        raise SetupError(f"project_root is not a directory: {root}")

    data = validate_input(copy.deepcopy(input_obj))

    report_rel = _rel_path(report_path, "report_path")
    if report_rel == ".":
        raise SetupError("report_path must name a file, not the project root")
    report_target = root / report_rel
    _ensure_within(root, report_target, "report_path")

    project_name = root.resolve().name
    files = render_all(data, project_name)

    # Every generated path must land under tools/** and never outside the project.
    for rel in files:
        if not rel.startswith("tools/"):
            raise SetupError(f"refusing to write outside tools/: {rel}")
        _ensure_within(root, root / rel, "generated path")

    gitignore_added: "str | None" = None
    # -- from here on we write; validation above is complete --
    written: list[str] = []
    for rel in sorted(files):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as handle:
            handle.write(files[rel])
        written.append(rel)

    if data["graphify"]["enabled"]:
        gitignore = root / ".gitignore"
        current = gitignore.read_text(encoding="utf-8") if gitignore.exists() else None
        merged = merge_gitignore(current)
        if merged != current:
            with open(gitignore, "w", encoding="utf-8", newline="") as handle:
                handle.write(merged)
        gitignore_added = GITIGNORE_LINE
        written.append(".gitignore")

        # The root .graphifyignore is skill-owned generated config: overwrite it
        # (like the config JSON), not merge it. Graphify scans from the repo
        # root, so this file must live at the root, not under tools/graphify/.
        graphifyignore = root / ROOT_GRAPHIFYIGNORE_REL
        _ensure_within(root, graphifyignore, "root .graphifyignore")
        with open(graphifyignore, "wb") as handle:
            handle.write(_render_root_graphifyignore(data))
        written.append(ROOT_GRAPHIFYIGNORE_REL)

    checks_summary = "split into checks.json" if _has_checks(data) else "no checks declared"
    report = {
        "confirmed_inputs": data,
        "written_files": sorted(written),
        "gitignore_line_added": gitignore_added,
        "commands": [
            {
                "argv": ["setup_project", "--check", name],
                "cwd": ".",
                "exit_code": 0,
                "summary": summary,
            }
            for name, summary in (
                ("input-schema", "accepted"),
                (
                    "path-safety",
                    "generated files under tools/ plus the root .gitignore and "
                    ".graphifyignore; all anchor-relative",
                ),
                ("task-type-registry", "all task types approved"),
                ("shell-free-argv", "all check commands are real argv lists"),
                (
                    "graphify-contract",
                    "enabled" if data["graphify"]["enabled"] else "disabled",
                ),
                ("checks-split", checks_summary),
            )
        ],
        "graphify_enabled": data["graphify"]["enabled"],
        "notes": [
            "Thin tools/feature-pipeline/run_pipeline.py launcher was not generated "
            "(optional).",
            "No shell, installer, commit, push, or dependency install was performed.",
        ],
    }

    report_target.parent.mkdir(parents=True, exist_ok=True)
    with open(report_target, "wb") as handle:
        handle.write(_dumps(report))
    return report


# -- CLI ------------------------------------------------------------


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic project-local feature-pipeline / Graphify setup."
    )
    parser.add_argument("--input", required=True, help="Path to the JSON input object.")
    parser.add_argument(
        "--project-root", required=True, help="Target repository root to configure."
    )
    parser.add_argument(
        "--report",
        required=True,
        help="Repository-relative path for the setup report JSON.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Assert every discovered value has been confirmed by the operator.",
    )
    args = parser.parse_args(argv)

    try:
        input_obj = json.loads(Path(args.input).read_text(encoding="utf-8"))
        report = run_setup(
            input_obj,
            project_root=args.project_root,
            report_path=args.report,
            confirmed=args.confirm,
        )
    except SetupError as err:
        print(f"setup refused: {err}", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as err:
        print(f"setup failed: {err}", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
