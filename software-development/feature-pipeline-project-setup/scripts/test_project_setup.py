"""Fixture-based tests for the deterministic project setup generator and the
read-only setup validator.

Written before ``setup_project.py`` / ``validate_project_setup.py`` per the
test-driven-development skill. Each generator negative case snapshots the target
tree first and asserts it is untouched after the expected
:class:`setup_project.SetupError`; each validator case builds a real generated
fixture, introduces exactly one defect, and asserts a single stable finding code
plus a byte-identical tree across the validation call.
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import setup_project
import validate_project_setup as vps
from setup_project import SetupError, run_setup


def _valid_input() -> dict:
    """A confirmed, fully specified input object (Graphify enabled)."""
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
                    },
                    {"name": "lint", "argv": ["ruff", "check", "."], "cwd": "."},
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
            "wrapper_source": None,  # filled in by the test with a real fixture dir
            "wrapper_destination": "tools/graphify/config/wrapper",
        },
    }


def _snapshot(root: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root)).replace(os.sep, "/")] = path.read_bytes()
    return out


class GeneratorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project = Path(self._tmp.name) / "target-repo"
        (self.project / "docs").mkdir(parents=True)
        (self.project / "feature-pipeline-skill" / "pipeline_core").mkdir(parents=True)
        (self.project / "feature-pipeline-skill" / "pipeline_core" / "profiles.py").write_text(
            "# portable core, must not be touched\n", encoding="utf-8"
        )
        (self.project / ".agents").mkdir()
        # An approved wrapper source outside the project.
        self.wrapper_src = Path(self._tmp.name) / "approved-wrapper"
        self.wrapper_src.mkdir()
        (self.wrapper_src / "build_graph.sh").write_text(
            "#!/bin/sh\nexec graphify build tools/graphify \"$@\"\n", encoding="utf-8"
        )

    def _input(self, **overrides) -> dict:
        data = _valid_input()
        data["graphify"]["wrapper_source"] = str(self.wrapper_src)
        for key, value in overrides.items():
            data[key] = value
        return data

    def _run(self, data: dict, *, confirmed: bool = True, report: str = "setup-report.json"):
        return run_setup(
            data,
            project_root=self.project,
            report_path=report,
            confirmed=confirmed,
        )

    # -- fresh generation --------------------------------------------------

    def test_fresh_generation_creates_full_layout(self) -> None:
        report = self._run(self._input())

        cfg = self.project / "tools" / "feature-pipeline" / "config"
        for name in ("pipeline.profile.json", "integrations.json", "checks.json"):
            self.assertTrue((cfg / name).is_file(), name)
        self.assertTrue((self.project / "tools" / "feature-pipeline" / "README.md").is_file())
        self.assertTrue((self.project / "tools" / "graphify" / ".graphifyignore").is_file())
        self.assertTrue(
            (self.project / "tools" / "graphify" / "config" / "wrapper" / "build_graph.sh").is_file()
        )
        self.assertTrue((self.project / "setup-report.json").is_file())

        profile = json.loads((cfg / "pipeline.profile.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["schema_version"], 1)
        self.assertEqual(
            [r["task_type"] for r in profile["task_routing"]], ["tooling", "docs"]
        )
        self.assertNotIn("checks", profile)  # split into checks.json, never both

        integrations = json.loads((cfg / "integrations.json").read_text(encoding="utf-8"))
        self.assertEqual(report["graphify_enabled"], True)
        self.assertEqual(integrations["graphify"]["workspace"], "tools/graphify")
        self.assertEqual(integrations["graphify"]["diff_policy"], "tracked-empty")

    def test_gitignore_line_added_once_and_preserves_content(self) -> None:
        gitignore = self.project / ".gitignore"
        gitignore.write_text("*.pyc\n/node_modules/\n\n# custom\n.env\n", encoding="utf-8")

        self._run(self._input())
        text = gitignore.read_text(encoding="utf-8")

        self.assertIn("*.pyc\n", text)
        self.assertIn("/node_modules/\n", text)
        self.assertIn("# custom\n", text)
        self.assertIn(".env\n", text)
        self.assertEqual(text.count("/tools/graphify/graphify-out/"), 1)

    def test_graphify_policy_contract(self) -> None:
        self._run(self._input())
        integrations = json.loads(
            (self.project / "tools/feature-pipeline/config/integrations.json").read_text("utf-8")
        )
        block = integrations["graphify"]
        self.assertEqual(
            block["expected_outputs"],
            [
                "tools/graphify/graphify-out/graph.json",
                "tools/graphify/graphify-out/GRAPH_REPORT.md",
                "tools/graphify/graphify-out/manifest.json",
                "tools/graphify/graphify-out/.graphify_labels.json",
                "tools/graphify/graphify-out/.graphify_root",
            ],
        )
        self.assertEqual(
            block["forbidden"],
            [
                "graphify claude install",
                "graphify codex install",
                "graphify antigravity install",
            ],
        )
        self.assertEqual(block["diff_policy"], "tracked-empty")
        joined = json.dumps(integrations)
        self.assertNotIn("graph.html", joined)
        self.assertNotIn('"tools/graphify"\n', joined)  # never ignore the whole tree

    # -- idempotency -----------------------------------------------------

    def test_idempotent_rerun_is_byte_identical(self) -> None:
        self.project.joinpath(".gitignore").write_text("*.log\n", encoding="utf-8")
        self._run(self._input())
        tracked = _snapshot(self.project / "tools")
        gitignore_first = (self.project / ".gitignore").read_bytes()

        self._run(self._input())

        self.assertEqual(_snapshot(self.project / "tools"), tracked)
        self.assertEqual((self.project / ".gitignore").read_bytes(), gitignore_first)
        self.assertEqual(
            (self.project / ".gitignore").read_text("utf-8").count("/tools/graphify/graphify-out/"),
            1,
        )

    # -- fail-closed cases (no writes) ---------------------------------

    def _assert_no_writes(
        self, data: dict, message: str, *, confirmed: bool = True
    ) -> SetupError:
        before = _snapshot(self.project)
        with self.assertRaises(SetupError, msg=message) as ctx:
            self._run(data, confirmed=confirmed)
        self.assertEqual(_snapshot(self.project), before, message)
        return ctx.exception

    def test_missing_confirmation_fails_closed(self) -> None:
        self._assert_no_writes(self._input(), "unconfirmed input", confirmed=False)

    def test_unknown_top_level_key_fails_closed(self) -> None:
        data = self._input()
        data["surprise"] = 1
        self._assert_no_writes(data, "unknown key")

    def test_missing_required_key_fails_closed(self) -> None:
        data = self._input()
        del data["run_state_path"]
        self._assert_no_writes(data, "missing run_state_path")

    def test_absolute_generated_path_fails_closed(self) -> None:
        data = self._input()
        data["run_state_path"] = "/var/run/pipeline"
        self._assert_no_writes(data, "absolute path")

    def test_parent_escape_path_fails_closed(self) -> None:
        data = self._input()
        data["task_routing"][0]["working_root"] = "../outside"
        self._assert_no_writes(data, "parent escape")

    def test_backslash_path_fails_closed(self) -> None:
        data = self._input()
        data["run_state_path"] = "tools\\feature-pipeline\\state"
        self._assert_no_writes(data, "backslash separator")

    def test_shell_form_check_command_fails_closed(self) -> None:
        data = self._input()
        data["technology_stacks"][0]["checks"][0]["argv"] = ["ruff check . && pytest"]
        self._assert_no_writes(data, "shell operator in argv")

    def test_string_check_command_fails_closed(self) -> None:
        data = self._input()
        data["technology_stacks"][0]["checks"][0]["argv"] = "ruff check ."
        self._assert_no_writes(data, "argv must be a list")

    def test_unapproved_task_type_fails_closed(self) -> None:
        data = self._input()
        data["task_routing"][0]["task_type"] = "deployment"
        self._assert_no_writes(data, "unapproved task type")

    def test_graphify_enabled_without_wrapper_source_fails_closed(self) -> None:
        data = self._input()
        data["graphify"]["wrapper_source"] = None
        self._assert_no_writes(data, "missing wrapper source")

    def test_unresolved_wrapper_source_fails_closed(self) -> None:
        data = self._input()
        data["graphify"]["wrapper_source"] = str(self.wrapper_src / "does-not-exist")
        self._assert_no_writes(data, "wrapper source does not resolve")

    def test_report_path_outside_project_fails_closed(self) -> None:
        before = _snapshot(self.project)
        with self.assertRaises(SetupError):
            self._run(self._input(), report="../escape-report.json")
        self.assertEqual(_snapshot(self.project), before)

    # -- Graphify disabled ---------------------------------------------

    def test_graphify_disabled_writes_no_graphify_tree(self) -> None:
        data = self._input(graphify={"enabled": False})
        self._run(data)

        self.assertFalse((self.project / "tools" / "graphify").exists())
        self.assertFalse((self.project / ".gitignore").exists())
        integrations = json.loads(
            (self.project / "tools/feature-pipeline/config/integrations.json").read_text("utf-8")
        )
        self.assertNotIn("graphify", integrations)

    # -- portable-core / no-shell-out guarantees (AC-5) ---------------

    def test_portable_core_is_untouched(self) -> None:
        core = self.project / "feature-pipeline-skill"
        before = _snapshot(core)
        self._run(self._input())
        self.assertEqual(_snapshot(core), before)

    def test_written_files_stay_within_tools_and_gitignore(self) -> None:
        report = self._run(self._input())
        for rel in report["written_files"]:
            self.assertTrue(
                rel == ".gitignore" or rel.startswith("tools/"),
                rel,
            )

    def test_generator_module_never_shells_out(self) -> None:
        source = Path(setup_project.__file__).read_text(encoding="utf-8")
        for banned in (
            "import subprocess",
            "subprocess.",
            "os.system",
            "os.popen",
            "os.exec",
            "os.spawn",
            "pty.",
            "__import__(",
        ):
            self.assertNotIn(banned, source, banned)

    def test_report_records_no_forbidden_commands(self) -> None:
        report = self._run(self._input())
        for command in report.get("commands", []):
            joined = " ".join(command["argv"])
            self.assertNotIn("install", joined)
            self.assertNotIn("commit", joined)
            self.assertNotIn("push", joined)


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
    )


class ValidatorTestCase(unittest.TestCase):
    """Read-only validator: one defect at a time, stable codes, no mutation."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project = Path(self._tmp.name) / "target-repo"
        (self.project / "docs").mkdir(parents=True)
        core = self.project / "feature-pipeline-skill" / "pipeline_core"
        core.mkdir(parents=True)
        (core / "profiles.py").write_text("# portable core\n", encoding="utf-8")
        (self.project / ".agents").mkdir()
        self.wrapper_src = Path(self._tmp.name) / "approved-wrapper"
        self.wrapper_src.mkdir()
        (self.wrapper_src / "build_graph.sh").write_text(
            "#!/bin/sh\nexec graphify build tools/graphify \"$@\"\n", encoding="utf-8"
        )
        self.assertEqual(_git(self.project, "init", "-q").returncode, 0)

        data = _valid_input()
        data["graphify"]["wrapper_source"] = str(self.wrapper_src)
        run_setup(
            data,
            project_root=self.project,
            report_path="docs/setup-report.json",
            confirmed=True,
        )
        self.assertEqual(_git(self.project, "add", "-A").returncode, 0)

        self.profile = self.project / "tools/feature-pipeline/config/pipeline.profile.json"
        self.integrations = self.project / "tools/feature-pipeline/config/integrations.json"
        self.checks = self.project / "tools/feature-pipeline/config/checks.json"
        self.gitignore = self.project / ".gitignore"

    # -- helpers --------------------------------------------------------

    def _validate(self):
        return vps.run_validation(
            self.project,
            self.project / ".agents",
            self.project / "feature-pipeline-skill",
        )

    def _codes(self, findings) -> set[str]:
        return {f.code for f in findings}

    def _patch_json(self, path: Path, mutate) -> None:
        obj = json.loads(path.read_text(encoding="utf-8"))
        mutate(obj)
        path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")

    def _assert_single(self, code: str) -> None:
        before = _snapshot(self.project)
        findings = self._validate()
        self.assertEqual(_snapshot(self.project), before, "validation mutated the tree")
        self.assertEqual(self._codes(findings), {code}, findings)

    # -- positive ------------------------------------------------------

    def test_valid_generated_tree_passes_and_is_readonly(self) -> None:
        before = _snapshot(self.project)
        findings = self._validate()
        self.assertEqual(findings, [], findings)
        self.assertEqual(_snapshot(self.project), before)

    def test_graph_html_present_is_not_an_error(self) -> None:
        out = self.project / "tools/graphify/graphify-out"
        out.mkdir(parents=True)
        (out / "graph.html").write_text("<html></html>\n", encoding="utf-8")
        self.assertEqual(self._validate(), [])

    def test_graphify_disabled_tree_passes(self) -> None:
        proj2 = Path(self._tmp.name) / "no-graphify"
        (proj2 / "docs").mkdir(parents=True)
        (proj2 / ".agents").mkdir()
        (proj2 / "feature-pipeline-skill").mkdir()
        _git(proj2, "init", "-q")
        data = _valid_input()
        data["graphify"] = {"enabled": False}
        run_setup(data, project_root=proj2, report_path="r.json", confirmed=True)
        _git(proj2, "add", "-A")
        self.assertEqual(
            vps.run_validation(
                proj2, proj2 / ".agents", proj2 / "feature-pipeline-skill"
            ),
            [],
        )

    def test_self_test_mode_exit_zero(self) -> None:
        self.assertEqual(vps.self_test(), 0)

    # -- structure / JSON / schema ----------------------------------

    def test_missing_required_file_fails(self) -> None:
        self.integrations.unlink()
        self._assert_single("E_STRUCTURE")

    def test_invalid_json_fails(self) -> None:
        self.profile.write_text("{ not valid json", encoding="utf-8")
        self._assert_single("E_JSON_SYNTAX")

    def test_schema_missing_key_fails(self) -> None:
        self._patch_json(self.profile, lambda o: o.pop("run_state_path"))
        self._assert_single("E_SCHEMA")

    def test_schema_bad_version_fails(self) -> None:
        self._patch_json(self.profile, lambda o: o.__setitem__("schema_version", 2))
        self._assert_single("E_SCHEMA")

    def test_inline_checks_in_profile_fails(self) -> None:
        self._patch_json(self.profile, lambda o: o.__setitem__("checks", []))
        self._assert_single("E_SCHEMA")

    # -- task routing / roles / paths ------------------------------

    def test_unknown_task_type_fails(self) -> None:
        self._patch_json(
            self.profile,
            lambda o: o["task_routing"][0].__setitem__("task_type", "deployment"),
        )
        self._assert_single("E_TASK_TYPE")

    def test_role_without_grants_fails(self) -> None:
        self._patch_json(
            self.profile, lambda o: o["roles"][0].__setitem__("min_grants", [])
        )
        self._assert_single("E_ROLE_GRANTS")

    def test_working_root_escape_fails(self) -> None:
        self._patch_json(
            self.profile,
            lambda o: o["task_routing"][0].__setitem__("working_root", "../evil"),
        )
        self._assert_single("E_PATH_ESCAPE")

    def test_absolute_run_state_fails(self) -> None:
        self._patch_json(
            self.profile, lambda o: o.__setitem__("run_state_path", "/var/run/pipe")
        )
        self._assert_single("E_PATH_ABSOLUTE")

    def test_backslash_path_fails(self) -> None:
        self._patch_json(
            self.profile,
            lambda o: o.__setitem__("run_state_path", "tools\\fp\\state"),
        )
        self._assert_single("E_PATH_BACKSLASH")

    def test_run_state_inside_core_fails(self) -> None:
        self._patch_json(
            self.profile,
            lambda o: o.__setitem__("run_state_path", "feature-pipeline-skill/state"),
        )
        self._assert_single("E_RUN_STATE_PLACEMENT")

    def test_anchor_mismatch_fails(self) -> None:
        self._patch_json(
            self.profile,
            lambda o: o["anchors"].__setitem__("core_root", "some/other/core"),
        )
        self._assert_single("E_ANCHOR_MISMATCH")

    # -- checks.json ---------------------------------------------------

    def test_shell_form_argv_in_checks_fails(self) -> None:
        self._patch_json(
            self.checks,
            lambda o: o["checks"][0].__setitem__("argv", ["ruff check . && pytest"]),
        )
        self._assert_single("E_ARGV_SHELL")

    def test_non_list_argv_in_checks_fails(self) -> None:
        self._patch_json(
            self.checks, lambda o: o["checks"][0].__setitem__("argv", "ruff check .")
        )
        self._assert_single("E_ARGV_TYPE")

    def test_check_cwd_escape_fails(self) -> None:
        self._patch_json(
            self.checks, lambda o: o["checks"][0].__setitem__("cwd", "../nope")
        )
        self._assert_single("E_PATH_ESCAPE")

    # -- graphify policy --------------------------------------------

    def test_graphify_workspace_wrong_fails(self) -> None:
        self._patch_json(
            self.integrations,
            lambda o: o["graphify"].__setitem__("workspace", "graphify"),
        )
        self._assert_single("E_GRAPHIFY_WORKSPACE")

    def test_graphify_missing_wrapper_dir_fails(self) -> None:
        import shutil

        shutil.rmtree(self.project / "tools/graphify/config/wrapper")
        self._assert_single("E_GRAPHIFY_WRAPPER_MISSING")

    def test_graphify_extra_output_fails(self) -> None:
        self._patch_json(
            self.integrations,
            lambda o: o["graphify"]["expected_outputs"].append(
                "tools/graphify/graphify-out/graph.html"
            ),
        )
        self._assert_single("E_GRAPHIFY_OUTPUTS")

    def test_graphify_missing_output_fails(self) -> None:
        self._patch_json(
            self.integrations,
            lambda o: o["graphify"]["expected_outputs"].pop(),
        )
        self._assert_single("E_GRAPHIFY_OUTPUTS")

    def test_graphify_diff_policy_wrong_fails(self) -> None:
        self._patch_json(
            self.integrations,
            lambda o: o["graphify"].__setitem__("diff_policy", "tracked"),
        )
        self._assert_single("E_GRAPHIFY_DIFF_POLICY")

    def test_graphify_forbidden_incomplete_fails(self) -> None:
        self._patch_json(
            self.integrations,
            lambda o: o["graphify"].__setitem__(
                "forbidden", ["graphify claude install"]
            ),
        )
        self._assert_single("E_GRAPHIFY_FORBIDDEN")

    # -- .gitignore --------------------------------------------------

    def test_gitignore_missing_rule_fails(self) -> None:
        self.gitignore.write_text("*.pyc\n", encoding="utf-8")
        self._assert_single("E_GITIGNORE_MISSING_RULE")

    def test_gitignore_broad_rule_fails(self) -> None:
        self.gitignore.write_text(
            "/tools/graphify/\n/tools/graphify/graphify-out/\n", encoding="utf-8"
        )
        self._assert_single("E_GITIGNORE_BROAD_RULE")

    # -- git tracking boundaries ----------------------------------

    def test_tracked_graphify_output_fails(self) -> None:
        out = self.project / "tools/graphify/graphify-out"
        out.mkdir(parents=True)
        (out / "graph.json").write_text("{}\n", encoding="utf-8")
        self.assertEqual(
            _git(self.project, "add", "-f", "tools/graphify/graphify-out/graph.json").returncode,
            0,
        )
        self._assert_single("E_GIT_TRACKED_OUTPUT")

    def test_ignored_configuration_fails(self) -> None:
        self.gitignore.write_text(
            "/tools/graphify/graphify-out/\n/tools/feature-pipeline/config/integrations.json\n",
            encoding="utf-8",
        )
        self._assert_single("E_GIT_CONFIG_IGNORED")

    def test_ignored_wrapper_fails(self) -> None:
        self.gitignore.write_text(
            "/tools/graphify/graphify-out/\n/tools/graphify/config/wrapper/\n",
            encoding="utf-8",
        )
        self._assert_single("E_GIT_CONFIG_IGNORED")


import smoke_project_setup as smoke

#: The sibling portable-core skill checkout, located relative to this test file
#: (never inferred from a home directory). Smoke integration cases skip when it
#: or its CLI is not present.
_CORE_ROOT = Path(__file__).resolve().parents[2] / "feature-pipeline"
_HAVE_CORE = (_CORE_ROOT / "scripts" / "run_pipeline.py").is_file()


class SmokeArgvGuardTestCase(unittest.TestCase):
    """Unit coverage for the pre-launch argv guard and report comparison."""

    def test_forbidden_argv_rejected_before_launch(self) -> None:
        for argv in (
            ["git", "commit", "-m", "x"],
            ["git", "push", "origin", "main"],
            ["python", "run_pipeline.py", "--push"],
            ["python", "run_pipeline.py", "--commit"],
            ["python", "run_pipeline.py", "--commit-approved-manifest"],
            ["graphify", "claude", "install"],
            ["graphify", "codex", "install"],
        ):
            with self.assertRaises(smoke.SmokeError, msg=argv):
                smoke.assert_argv_allowed(argv)

    def test_allowed_argv_passes(self) -> None:
        for argv in (
            ["git", "init", "-q"],
            ["git", "add", "-A"],
            ["python", "run_pipeline.py", "--help"],
            ["python", "run_pipeline.py", "--mode", "plan-only", "--dry-run"],
        ):
            smoke.assert_argv_allowed(argv)  # must not raise

    def test_reports_match_detects_difference(self) -> None:
        self.assertTrue(smoke.reports_match({"a": 1, "b": [1, 2]}, {"b": [1, 2], "a": 1}))
        self.assertFalse(smoke.reports_match({"a": 1}, {"a": 2}))

    def test_build_core_inputs_consumes_generated_setup(self) -> None:
        generated_profile = {
            "project": "demo",
            "anchors": {"agents_root": ".agents", "core_root": "feature-pipeline-skill"},
            "task_routing": [
                {"task_type": "tooling", "working_root": "tools"},
                {"task_type": "docs", "working_root": "docs"},
            ],
            "run_state_path": "tools/feature-pipeline/state",
            "roles": [{"role": "executor", "min_grants": ["read", "write"]}],
        }
        generated_checks = {
            "checks": [
                {"stack": "python", "name": "unit", "argv": ["uv", "run", "pytest"], "cwd": "."}
            ]
        }
        profile, plan = smoke.build_core_inputs(generated_profile, generated_checks)

        self.assertEqual(profile["version"], 1)
        self.assertEqual(profile["name"], "demo")
        self.assertEqual(sorted(profile["registry"]["task_types"]), ["docs", "tooling"])
        self.assertEqual(profile["registry"]["roots"], {"tooling": "tools", "docs": "docs"})
        self.assertEqual(profile["registry"]["checks"], {"unit": ["uv", "run", "pytest"]})
        self.assertEqual(
            profile["registry"]["storage"], {"run_state": "tools/feature-pipeline/state"}
        )
        self.assertEqual([t["type"] for t in plan["tasks"]], ["tooling", "docs"])
        self.assertEqual(plan["tasks"][1]["depends_on"], ["SM-01"])

    def test_build_core_inputs_rejects_empty_routing(self) -> None:
        with self.assertRaises(smoke.SmokeError):
            smoke.build_core_inputs(
                {"project": "x", "anchors": {"agents_root": "a", "core_root": "c"},
                 "task_routing": [], "run_state_path": "s", "roles": []},
                None,
            )


@unittest.skipUnless(_HAVE_CORE, "portable core checkout not present next to the skill")
class SmokeHarnessTestCase(unittest.TestCase):
    """Integration coverage: the harness drives the real portable core CLI."""

    def test_successful_smoke_self_test(self) -> None:
        self.assertEqual(smoke.self_test(core_root=_CORE_ROOT), 0)

    def test_capture_is_deterministic_and_touches_nothing_forbidden(self) -> None:
        report = smoke.capture(core_root=_CORE_ROOT)
        self.assertEqual(report["core"]["help"]["exit"], smoke.EXPECTED_HELP_EXIT)
        self.assertEqual(report["core"]["dry_run"]["exit"], smoke.EXPECTED_DRY_RUN_EXIT)
        self.assertTrue(report["exit_contract"]["satisfied"])
        self.assertFalse(report["graphify_executed"])
        self.assertTrue(report["outside_tmp_unchanged"])
        self.assertEqual(report["validation"]["findings"], [])
        for argv in report["launched_argv"]:
            joined = " ".join(argv).lower()
            self.assertNotIn("commit", joined)
            self.assertNotIn("push", joined)
            self.assertNotIn("install", joined)
            self.assertNotIn("graphify", joined)
        # The dry run is the core's only planning execution and it stayed a plan.
        self.assertIn("dry run", report["core"]["dry_run"]["stdout"])
        self.assertIn("C5. Exit code: 10", report["core"]["dry_run"]["stdout"])

    def test_core_non_zero_exit_fails_the_smoke(self) -> None:
        def tamper(profile: dict, plan: dict) -> "tuple[dict, dict]":
            return profile, {**plan, "tasks": [{"id": "SM-01", "type": "not_a_real_type"}]}

        with self.assertRaises(smoke.SmokeError) as ctx:
            smoke.capture(core_root=_CORE_ROOT, _tamper=tamper)
        self.assertIn("dry-run exit contract", str(ctx.exception))

    def test_out_of_fixture_mutation_is_detected(self) -> None:
        real = smoke.tree_hashes
        seen: list[int] = []

        def drifting(root: Path) -> "dict[str, str]":
            seen.append(1)
            # First call (the "before" snapshot) and every later call disagree.
            return {"sentinel": str(len(seen))}

        smoke.tree_hashes = drifting  # type: ignore[assignment]
        try:
            with self.assertRaises(smoke.SmokeError) as ctx:
                smoke.capture(core_root=_CORE_ROOT)
        finally:
            smoke.tree_hashes = real  # type: ignore[assignment]
        self.assertIn("outside its temp dir", str(ctx.exception))

    def test_nondeterministic_report_is_detected(self) -> None:
        self.assertEqual(
            smoke.self_test(core_root=_CORE_ROOT, _nondeterministic=True), 1
        )


if __name__ == "__main__":
    unittest.main()
