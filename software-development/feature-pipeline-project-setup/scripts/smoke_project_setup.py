"""Isolated smoke harness for the feature-pipeline project setup skill.

This is **not** a Graphify build. In one fresh temporary directory it:

1. creates a complete minimal fixture project (its own Git work tree, a stub
   portable-core tree, an approved wrapper source),
2. applies :mod:`setup_project` to generate the project-local ``tools/**``
   configuration,
3. runs :mod:`validate_project_setup` read-only over that generated tree,
4. derives a portable-core profile and plan **from the generated setup output**,
5. invokes the explicitly located portable core CLI twice and only twice --
   ``--help`` and one ``--mode plan-only --dry-run`` scenario -- and checks the
   documented exit contract (``0`` for help, ``10`` for a non-blocked dry run),
6. snapshots every path outside the temporary directory the run can reach and
   fails if any byte changed,
7. captures stable, redacted, timing-free evidence and proves two self-test
   runs produce byte-identical normalized reports.

The harness never runs a Graphify installer, never runs the Graphify wrapper,
never creates a commit or a push, and never installs a dependency. Every
subprocess argv is a shell-free list vetted by :func:`assert_argv_allowed`
*before* launch; a forbidden token (a Graphify installer, ``commit``, ``push``)
raises before any process starts.

Both the portable ``--core-root`` and the optional ``--agents-root`` are passed
explicitly. Neither is ever inferred from the current working directory or a
user's home directory.

Usage::

    python smoke_project_setup.py --self-test --core-root <feature-pipeline checkout>
    python smoke_project_setup.py --self-test --core-root <...> --agents-root <...>

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Sequence

import setup_project
import validate_project_setup as vps


class SmokeError(Exception):
    """Raised for any smoke-contract violation. Every raise is fail-closed."""


class BlockingCondition(Exception):
    """Raised when the portable core cannot be resolved or does not expose the
    ``plan-only --dry-run`` path. Maps to CLI exit ``2`` (a bad invocation)."""


# -- exit contract ---------------------------------------------------------

#: ``run_pipeline.py --help`` exits ``0``.
EXPECTED_HELP_EXIT = 0
#: A non-blocked ``--mode plan-only --dry-run`` stops with a delivery gate
#: pending; the portable core and the MI-01 exit table return ``10``.
EXPECTED_DRY_RUN_EXIT = 10

#: Directory names skipped by every tree snapshot -- caches and VCS metadata are
#: not part of a byte-for-byte "did the smoke touch this tree" check.
_SKIP_DIRS = frozenset(
    {".git", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", "node_modules"}
)

#: argv tokens a smoke subprocess may never carry.
_FORBIDDEN_ARGV_TOKENS = frozenset(
    {"commit", "push", "tag", "--commit", "--commit-approved-manifest", "--push"}
)


# -- argv safety ---------------------------------------------------------


def assert_argv_allowed(argv: "Sequence[str]") -> None:
    """Reject a subprocess argv that would install Graphify, commit, or push.

    Raises :class:`SmokeError` before the caller can launch anything.
    """
    tokens = [str(token) for token in argv]
    lowered = [token.lower() for token in tokens]

    if "graphify" in lowered and "install" in lowered:
        raise SmokeError(f"refusing a Graphify installer argv: {tokens}")
    for token in lowered:
        if token in _FORBIDDEN_ARGV_TOKENS:
            raise SmokeError(f"refusing an argv containing {token!r}: {tokens}")
    if lowered[:1] == ["git"] and len(lowered) > 1 and lowered[1] in {"commit", "push", "tag"}:
        raise SmokeError(f"refusing a mutating git argv: {tokens}")


# -- core inputs derived from the generated setup output ------------------


def build_core_inputs(
    generated_profile: dict, generated_checks: "dict | None"
) -> "tuple[dict, dict]":
    """Translate the generated project-local setup into a portable-core profile
    and plan.

    The portable core carries no project identity: it wants a ``version`` /
    ``name`` / ``logical_paths`` / ``role_grants`` / ``stages`` / ``registry``
    profile. Every project literal in the result -- the task types, their
    working roots, the check argv, the role grants, the run-state location --
    comes straight from what :mod:`setup_project` wrote, so a dry run over it
    genuinely exercises *setup output* driving the core.
    """
    routing = generated_profile["task_routing"]
    if not routing:
        raise SmokeError("generated profile has no task_routing to drive the core with")
    roles = generated_profile["roles"]
    run_state_path = generated_profile["run_state_path"]
    anchors = generated_profile["anchors"]

    check_entries = list((generated_checks or {}).get("checks", []))
    checks_registry = {entry["name"]: list(entry["argv"]) for entry in check_entries}
    check_names = sorted(checks_registry)
    stack_names = sorted({entry["stack"] for entry in check_entries}) or ["default"]

    roots_registry = {entry["task_type"]: entry["working_root"] for entry in routing}
    task_types = {
        entry["task_type"]: {
            "stack": stack_names[0],
            "subagents": ["executor"],
            "root": entry["task_type"],
            "checks": check_names,
            "storage": "run_state",
        }
        for entry in routing
    }

    profile = {
        "version": 1,
        "name": generated_profile["project"],
        "logical_paths": {
            "project": ".",
            "agents": anchors["agents_root"],
            "core": anchors["core_root"],
        },
        "role_grants": {role["role"]: list(role["min_grants"]) for role in roles},
        "stages": [
            {"name": "implement", "subagents": ["executor"], "argv": ["setup", "plan-only"]}
        ],
        "registry": {
            "task_types": task_types,
            "stacks": {name: {"runtime": name} for name in stack_names},
            "subagents": {"executor": {"grant": "executor"}},
            "roots": roots_registry,
            "checks": checks_registry,
            "storage": {"run_state": run_state_path},
        },
    }

    tasks: list[dict] = []
    for index, entry in enumerate(routing, start=1):
        task = {"id": f"SM-{index:02d}", "type": entry["task_type"]}
        if index > 1:
            task["depends_on"] = [f"SM-{index - 1:02d}"]
        tasks.append(task)
    plan = {"feature": "setup-smoke", "tasks": tasks}
    return profile, plan


# -- redaction / normalization -----------------------------------------


def _spellings(path: Path) -> list[str]:
    native = str(path)
    return [native, native.replace("\\", "/"), native.replace("\\", "\\\\"), path.as_posix()]


def _replacements(*, tmp: Path, core_root: Path, agents_root: Path) -> "list[tuple[str, str]]":
    ordered: list[tuple[Path, str]] = [
        (agents_root, "<agents_root>"),
        (core_root, "<core_root>"),
        (tmp, "<tmp>"),
        (Path.home(), "<home>"),
    ]
    rules: list[tuple[str, str]] = []
    for path, token in ordered:
        for spelling in _spellings(path.resolve()):
            if len(spelling) >= 3:
                rules.append((spelling, token))
    # Longest match first so a nested anchor never collapses to the wrong token.
    rules.sort(key=lambda item: len(item[0]), reverse=True)
    return rules


def normalize_text(text: str, rules: "Sequence[tuple[str, str]]") -> str:
    """Replace every machine-local path spelling with a stable logical token and
    strip the random suffix the core's throwaway dry-run directory carries."""
    out = text
    for needle, token in rules:
        out = out.replace(needle, token)
    out = re.sub(r"pipeline-dry-run-[A-Za-z0-9_]+", "pipeline-dry-run-<id>", out)
    return out


def _normalize_argv(argv: "Sequence[str]", rules: "Sequence[tuple[str, str]]") -> list[str]:
    normalized: list[str] = []
    for token in argv:
        value = normalize_text(str(token), rules)
        if "<" in value and ">" in value:
            # A path token that now carries a logical anchor: make the rest of it
            # POSIX so the report is byte-identical regardless of host separator.
            value = value.replace("\\", "/")
        if value.endswith("run_pipeline.py"):
            value = "<core_root>/scripts/run_pipeline.py"
        elif value.endswith(("python.exe", "python", "python3", "python3.exe")):
            value = "<python>"
        normalized.append(value)
    return normalized


# -- tree snapshots ---------------------------------------------------


def tree_hashes(root: Path) -> "dict[str, str]":
    """Map every non-cache file under ``root`` to a sha256 of its bytes."""
    out: dict[str, str] = {}
    if not root.exists():
        return out
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in _SKIP_DIRS for part in rel.parts):
            continue
        if path.is_file():
            out[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


# -- subprocess plumbing ----------------------------------------------


def _utf8_env() -> "dict[str, str]":
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    return env


def _run(argv: "Sequence[str]", *, cwd: Path, launched: "list[list[str]]") -> subprocess.CompletedProcess:
    assert_argv_allowed(argv)
    launched.append([str(token) for token in argv])
    return subprocess.run(
        list(argv),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        env=_utf8_env(),
    )


# -- fixture ---------------------------------------------------------


def _smoke_input(wrapper_source: str) -> dict:
    """A confirmed setup input for a minimal but complete fixture project."""
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
        "roles": [
            {"role": "executor", "min_grants": ["read", "write"]},
            {"role": "task_verifier", "min_grants": ["read"]},
        ],
        "graphify": {
            "enabled": True,
            "wrapper_source": wrapper_source,
            "wrapper_destination": "tools/graphify/config/wrapper",
            "index_excludes": ["docs/fixtures", "feature-pipeline-skill/fixtures"],
        },
    }


def _seed_fixture(tmp: Path, launched: "list[list[str]]") -> Path:
    """Build the fixture project tree inside ``tmp`` and return its root."""
    project = tmp / "fixture"
    (project / "docs").mkdir(parents=True)
    core_stub = project / "feature-pipeline-skill" / "pipeline_core"
    core_stub.mkdir(parents=True)
    (core_stub / "profiles.py").write_text("# portable core stub\n", encoding="utf-8")
    (project / ".agents").mkdir()

    wrapper_src = tmp / "wrapper-src"
    wrapper_src.mkdir()
    (wrapper_src / "build_graph.sh").write_text(
        '#!/bin/sh\nexport GRAPHIFY_OUT="$PWD/tools/graphify/graphify-out"\n'
        'exec graphify update . "$@"\n',
        encoding="utf-8",
    )

    init = _run(["git", "init", "-q"], cwd=project, launched=launched)
    if init.returncode != 0:
        raise SmokeError(f"could not 'git init' the fixture: {init.stderr.strip()}")

    setup_project.run_setup(
        _smoke_input(str(wrapper_src)),
        project_root=project,
        report_path="docs/setup-report.json",
        confirmed=True,
    )
    add = _run(["git", "add", "-A"], cwd=project, launched=launched)
    if add.returncode != 0:
        raise SmokeError(f"could not stage the generated fixture: {add.stderr.strip()}")
    return project


# -- core resolution -------------------------------------------------


def resolve_core_cli(core_root: "str | Path") -> Path:
    """Return the portable core runner script, or raise :class:`BlockingCondition`."""
    root = Path(core_root).resolve()
    if not root.is_dir():
        raise BlockingCondition(f"--core-root is not a directory: {root}")
    runner = root / "scripts" / "run_pipeline.py"
    if not runner.is_file():
        raise BlockingCondition(
            f"--core-root does not expose scripts/run_pipeline.py: {root}"
        )
    return runner


# -- one full capture ----------------------------------------------


def capture(
    *,
    core_root: "str | Path",
    agents_root: "str | Path | None" = None,
    _tamper: "Callable[[dict, dict], tuple[dict, dict]] | None" = None,
    _nondeterministic: bool = False,
) -> dict:
    """Run the whole smoke once in a fresh temp dir and return a normalized,
    timing-free report. Raises :class:`SmokeError` on any contract violation and
    :class:`BlockingCondition` when the core cannot be resolved.

    ``_tamper`` and ``_nondeterministic`` are test-only seams.
    """
    runner = resolve_core_cli(core_root)
    core_root_path = runner.parents[1]
    external_agents = Path(agents_root).resolve() if agents_root is not None else None

    launched: list[list[str]] = []
    with tempfile.TemporaryDirectory(prefix="setup-smoke-") as tmp_name:
        tmp = Path(tmp_name).resolve()

        outside_before = {
            "<core_root>": tree_hashes(core_root_path),
        }
        if external_agents is not None and not _is_within(external_agents, tmp):
            outside_before["<agents_root>"] = tree_hashes(external_agents)

        project = _seed_fixture(tmp, launched)

        # -- read-only validation of the pure generated tree --
        fixture_agents = project / ".agents"
        fixture_core = project / "feature-pipeline-skill"
        findings = vps.run_validation(project, fixture_agents, fixture_core)
        if findings:
            raise SmokeError(
                "generated setup fails its own validator: "
                + ", ".join(f"{f.code}:{f.detail}" for f in findings)
            )

        # -- derive the core inputs from the generated setup output --
        generated_profile = json.loads(
            (project / "tools/feature-pipeline/config/pipeline.profile.json").read_text("utf-8")
        )
        checks_path = project / "tools/feature-pipeline/config/checks.json"
        generated_checks = (
            json.loads(checks_path.read_text("utf-8")) if checks_path.is_file() else None
        )
        core_profile, core_plan = build_core_inputs(generated_profile, generated_checks)
        if _tamper is not None:
            core_profile, core_plan = _tamper(core_profile, core_plan)
        (project / "core.profile.json").write_text(
            json.dumps(core_profile, indent=2) + "\n", encoding="utf-8"
        )
        (project / "core.plan.json").write_text(
            json.dumps(core_plan, indent=2) + "\n", encoding="utf-8"
        )

        # -- the smoke's only two core executions --
        anchor_argv = [
            "--project-root", str(project),
            "--agents-root", str(external_agents or fixture_agents),
            "--core-root", str(core_root_path),
        ]
        help_proc = _run(
            [sys.executable, str(runner), "--help"], cwd=core_root_path, launched=launched
        )
        _assert_core_exposes_dry_run(help_proc)
        if help_proc.returncode != EXPECTED_HELP_EXIT:
            raise SmokeError(
                f"core --help exit contract: expected {EXPECTED_HELP_EXIT}, "
                f"got {help_proc.returncode}"
            )

        dry_argv = [
            sys.executable, str(runner), *anchor_argv,
            "--profile", "core.profile.json",
            "--plan", "core.plan.json",
            "--mode", "plan-only", "--dry-run",
        ]
        dry_proc = _run(dry_argv, cwd=core_root_path, launched=launched)
        if dry_proc.returncode != EXPECTED_DRY_RUN_EXIT:
            raise SmokeError(
                f"core plan-only --dry-run exit contract: expected "
                f"{EXPECTED_DRY_RUN_EXIT}, got {dry_proc.returncode}\n{dry_proc.stderr}"
            )

        # -- prove nothing outside the temp dir moved --
        outside_after = {"<core_root>": tree_hashes(core_root_path)}
        if "<agents_root>" in outside_before:
            outside_after["<agents_root>"] = tree_hashes(external_agents)  # type: ignore[arg-type]
        changed = sorted(k for k in outside_before if outside_before[k] != outside_after.get(k))
        if changed:
            raise SmokeError(f"the smoke mutated a path outside its temp dir: {changed}")

        rules = _replacements(
            tmp=tmp, core_root=core_root_path, agents_root=external_agents or (project / ".agents")
        )
        graphify_ran = any(
            "graphify" in [t.lower() for t in argv] and "install" not in [t.lower() for t in argv]
            and not any(t.endswith(("run_pipeline.py",)) for t in argv)
            for argv in launched
        )
        report = {
            "scenario": "setup -> validate -> core plan-only --dry-run",
            "setup": {
                "written_files": sorted(
                    json.loads((project / "docs/setup-report.json").read_text("utf-8"))[
                        "written_files"
                    ]
                ),
                "gitignore_line_added": setup_project.GITIGNORE_LINE,
                "graphify_enabled": True,
            },
            "validation": {"findings": []},
            "core_inputs_from_setup": {
                "profile_name": core_profile["name"],
                "task_types": sorted(core_profile["registry"]["task_types"]),
                "check_argv": {
                    name: argv for name, argv in core_profile["registry"]["checks"].items()
                },
                "storage": core_profile["registry"]["storage"],
                "plan_tasks": [
                    {"id": t["id"], "type": t["type"]} for t in core_plan["tasks"]
                ],
            },
            "core": {
                "help": {
                    "argv": _normalize_argv([sys.executable, str(runner), "--help"], rules),
                    "cwd": "<core_root>",
                    "exit": help_proc.returncode,
                },
                "dry_run": {
                    "argv": _normalize_argv(dry_argv, rules),
                    "cwd": "<core_root>",
                    "exit": dry_proc.returncode,
                    "stdout": normalize_text(dry_proc.stdout, rules),
                    "stderr": normalize_text(dry_proc.stderr, rules),
                },
            },
            "exit_contract": {
                "help": EXPECTED_HELP_EXIT,
                "dry_run": EXPECTED_DRY_RUN_EXIT,
                "satisfied": True,
            },
            "launched_argv": [_normalize_argv(argv, rules) for argv in launched],
            "graphify_executed": graphify_ran,
            "outside_tmp_paths_checked": sorted(outside_before),
            "outside_tmp_unchanged": True,
        }
        if graphify_ran:
            raise SmokeError("a Graphify wrapper/CLI was executed by the smoke harness")
        if _nondeterministic:
            report["_nondeterministic_probe"] = _os_urandom_token()
        return report


def _assert_core_exposes_dry_run(help_proc: subprocess.CompletedProcess) -> None:
    text = f"{help_proc.stdout}\n{help_proc.stderr}"
    if "plan-only" not in text or "--dry-run" not in text:
        raise BlockingCondition(
            "the portable core does not expose 'plan-only' and '--dry-run'"
        )


def _os_urandom_token() -> str:
    return hashlib.sha256(os.urandom(16)).hexdigest()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


# -- self test -----------------------------------------------------


def reports_match(first: dict, second: dict) -> bool:
    """True when two capture reports are byte-identical once serialized."""
    return json.dumps(first, indent=2, sort_keys=True) == json.dumps(
        second, indent=2, sort_keys=True
    )


def self_test(
    *,
    core_root: "str | Path",
    agents_root: "str | Path | None" = None,
    _nondeterministic: bool = False,
) -> int:
    """Run the smoke twice from independent temp dirs, prove the normalized
    reports are identical, print the report, and return ``0`` / ``1``."""
    first = capture(
        core_root=core_root, agents_root=agents_root, _nondeterministic=_nondeterministic
    )
    second = capture(
        core_root=core_root, agents_root=agents_root, _nondeterministic=_nondeterministic
    )
    identical = reports_match(first, second)
    print(
        json.dumps(
            {
                "report": first,
                "repeated_normalized_report_identical": identical,
                "exit_contract_satisfied": first["exit_contract"]["satisfied"],
                "graphify_executed": first["graphify_executed"],
                "outside_tmp_unchanged": first["outside_tmp_unchanged"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if (
        identical
        and first["exit_contract"]["satisfied"]
        and not first["graphify_executed"]
        and first["outside_tmp_unchanged"]
    ) else 1


# -- CLI ---------------------------------------------------------


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Isolated smoke harness: generate a project setup, validate it, and "
            "drive the portable core's plan-only --dry-run path in a disposable fixture."
        )
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run the full smoke twice in temporary directories and print the "
        "normalized report",
    )
    parser.add_argument(
        "--core-root",
        required=True,
        help="explicit portable feature-pipeline checkout (never inferred)",
    )
    parser.add_argument(
        "--agents-root",
        help="explicit shared agents checkout (optional; never inferred)",
    )
    args = parser.parse_args(argv)

    if not args.self_test:
        print("error: --self-test is required (it is the only mode)", file=sys.stderr)
        return 2

    try:
        return self_test(core_root=args.core_root, agents_root=args.agents_root)
    except BlockingCondition as err:
        print(f"smoke blocked: {err}", file=sys.stderr)
        return 2
    except SmokeError as err:
        print(f"smoke failed: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
